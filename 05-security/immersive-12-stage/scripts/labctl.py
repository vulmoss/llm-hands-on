"""Own-project Docker lifecycle; digest lock is required before any deployment."""

import argparse
import json
import os
import re
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

COURSE = Path(__file__).resolve().parents[1]
ROOT = COURSE.parents[1]
PROJECT = "llm-immersion"
SEEDS = {
    "DVWA_IMAGE": "ghcr.io/digininja/dvwa:latest",
    "DB_IMAGE": "docker.io/library/mariadb:10.11",
    "JUICE_IMAGE": "docker.io/bkimminich/juice-shop:v20.2.0",
}
REPOS = {
    "DVWA_IMAGE": "ghcr.io/digininja/dvwa",
    "DB_IMAGE": "mariadb",
    "JUICE_IMAGE": "bkimminich/juice-shop",
}


def docker(*args, env=None):
    return subprocess.check_output(["docker", *args], text=True, env=env).strip()


def canonical(repo):
    return repo.removeprefix("docker.io/").removeprefix("library/")


def validated_image(key, ref):
    repo, sep, digest = ref.partition("@")
    if canonical(repo) != REPOS[key] or not sep or not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
        raise ValueError(f"Invalid official digest for {key}")
    return ref


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def runtime_check():
    context = json.loads(docker("context", "inspect"))[0]
    hosts = [context["Endpoints"]["docker"]["Host"]]
    if os.environ.get("DOCKER_HOST"):
        hosts.append(os.environ["DOCKER_HOST"])
    if any(not host.startswith("unix://") for host in hosts):
        raise ValueError("Use a local Unix-socket Docker daemon on the lab host")
    version = docker("version", "--format", "{{.Server.Version}}")
    if int(version.split(".")[0]) < 28:
        raise ValueError(
            "This runbook requires Docker Engine 28+ for loopback publication behavior"
        )
    compose = docker("compose", "version", "--short").lstrip("v")
    numbers = tuple(int(n) for n in re.findall(r"\d+", compose)[:2])
    if numbers < (2, 24):
        raise ValueError("Docker Compose >=2.24 required")
    return {"docker": version, "compose": compose, "context": context["Name"]}


def lock_images(state):
    target = state / "images.lock.json"
    if target.exists():
        raise ValueError(
            "Lock already exists; preserve it and use a new state directory for upgrades"
        )
    runtime_check()
    records = {}
    for key, seed in SEEDS.items():
        subprocess.run(["docker", "pull", "--platform=linux/amd64", seed], check=True)
        item = json.loads(docker("image", "inspect", seed))[0]
        if item.get("Os") != "linux" or item.get("Architecture") != "amd64":
            raise ValueError(f"Wrong architecture for {seed}")
        matches = [
            x for x in item.get("RepoDigests", []) if canonical(x.split("@")[0]) == REPOS[key]
        ]
        if not matches:
            raise ValueError(f"No verified RepoDigest for {seed}")
        records[key] = {"seed": seed, "image": validated_image(key, matches[0]), "id": item["Id"]}
    write_json(
        target,
        {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "platform": "linux/amd64",
            "images": records,
        },
    )
    print(target)


def locked_env(state):
    data = json.loads((state / "images.lock.json").read_text())
    if data.get("platform") != "linux/amd64" or set(data["images"]) != set(SEEDS):
        raise ValueError("Invalid image lock")
    env = dict(os.environ, LAB_STATE=str(state))
    for key in SEEDS:
        env[key] = validated_image(key, data["images"][key]["image"])
    return env


def check_ownership(state):
    ids = docker("ps", "-aq", "--filter", f"label=com.docker.compose.project={PROJECT}").split()
    if ids:
        for item in json.loads(docker("inspect", *ids)):
            labels = item.get("Config", {}).get("Labels", {})
            if labels.get("org.llm-hands-on.state") != str(state):
                raise ValueError(
                    "Project name already belongs to another state directory; do not overwrite"
                )


def compose(state, target, *args):
    runtime_check()
    env = locked_env(state)
    check_ownership(state)
    cmd = [
        "docker",
        "compose",
        "--env-file",
        os.devnull,
        "-p",
        PROJECT,
        "-f",
        str(COURSE / "compose.json"),
    ]
    for profile in ["dvwa", "juice"] if target == "both" else [target]:
        cmd += ["--profile", profile]
    subprocess.run(cmd + list(args), check=True, env=env)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command", choices=["plan", "preflight", "lock", "config", "up", "status", "stop", "down"]
    )
    parser.add_argument("--target", choices=["dvwa", "juice", "both"], default="dvwa")
    parser.add_argument("--state", type=Path, default=ROOT / ".data/immersion")
    args = parser.parse_args(argv)
    state = args.state.expanduser().resolve()
    try:
        if args.command == "plan":
            print(
                json.dumps(
                    {
                        "project": PROJECT,
                        "state": str(state),
                        "seeds_not_locks": SEEDS,
                        "ports": {"dvwa": "127.0.0.1:4280", "juice": "127.0.0.1:4300"},
                    },
                    indent=2,
                )
            )
        elif args.command == "preflight":
            print(json.dumps(runtime_check(), indent=2))
            check_ownership(state)
        elif args.command == "lock":
            lock_images(state)
        elif args.command == "up":
            runtime_check()
            check_ownership(state)
            # Docker itself checks conflicts on up. Never kill unknown listeners.
            for port in (
                [4280, 4300] if args.target == "both" else [4280 if args.target == "dvwa" else 4300]
            ):
                with socket.socket() as sock:
                    if sock.connect_ex(("127.0.0.1", port)) == 0:
                        raise ValueError(
                            f"Port {port} is occupied; inspect/stop own project before restarting"
                        )
            compose(
                state, args.target, "up", "-d", "--wait", "--wait-timeout", "180", "--pull", "never"
            )
        elif args.command == "config":
            compose(state, args.target, "config", "--quiet")
            print("Compose resolved successfully")
        elif args.command == "status":
            compose(state, args.target, "ps", "--all")
        elif args.command == "stop":
            services = (
                ["dvwa", "db", "juice"]
                if args.target == "both"
                else (["dvwa", "db"] if args.target == "dvwa" else ["juice"])
            )
            compose(state, args.target, "stop", *services)
        elif args.command == "down":
            compose(state, "both", "down")  # Deliberately does not accept -v.
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

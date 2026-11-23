"""Read labels from the review bound to an exported sample, checking the manifest."""

from truncator.common.storage import read, digest, contained
from truncator.review.review_policy import validate_observation_labels
from truncator.review.review_evidence import validate_single_review
from truncator.common.capture_files import evidence_files


def reviewed_observation(root, folder, sample, member):
    if "application" in sample:
        review = read(contained(root, "applications/" + sample["application"] + "/review.json"))
        if member is not None and review["decisions"].get(member["id"], {}).get("decision") != "keep":
            raise ValueError("Combined exported target lacks a kept review")
        observation = review["decisions"][member["id"]] if member else {}
        if member is None:
            from truncator.planning.composition import capture_members
            plan = read(folder / "plan.json")
            if capture_members(plan, read(folder / "capture.json").get("recipe", {})):
                raise ValueError("Exported page omitted its planned mutation targets")
        captures = [c for c in review["captures"] if c["page"] == sample["page"]]
        if len(captures) != 1:
            raise ValueError("Exported page has no unique reviewed capture")
        if set(captures[0]["files"]) != set(evidence_files(folder)):
            raise ValueError("Exported review must bind all four capture files")
        for name, checksum in captures[0]["files"].items():
            if digest(contained(folder, name).read_bytes()) != checksum:
                raise ValueError("Exported reviewed capture changed")
        declared = sample.get("target_observations", {}).get(member["id"], {}) if member else {}
    else:
        observation = read(folder / "review.json")
        if observation.get("decision") != "accepted":
            raise ValueError("Exported sample lacks an accepted visual review")
        validate_single_review(folder, observation, exported=True)
        declared = sample
    content, recovery = observation.get("content_status"), observation.get("recovery_status")
    validate_observation_labels(content, recovery)
    if declared.get("content_status") != content or declared.get("recovery_status") != recovery:
        raise ValueError("Manifest labels differ from their bound visual review")
    return content, recovery

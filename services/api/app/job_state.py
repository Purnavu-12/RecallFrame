from dataclasses import dataclass


STAGES = ("queued", "validating", "downloading", "extracting_audio", "transcribing", "visual_analysis", "indexing", "ready", "failed")
TERMINAL = {"ready", "failed"}


@dataclass(frozen=True)
class JobSnapshot:
    status: str
    stage: str
    retry_count: int = 0


def transition(current: JobSnapshot, stage: str) -> JobSnapshot:
    if stage not in STAGES:
        raise ValueError(f"Unknown processing stage: {stage}")
    if current.stage in TERMINAL:
        raise ValueError(f"Cannot transition terminal job from {current.stage}")
    if stage == "failed":
        return JobSnapshot("failed", stage, current.retry_count)
    if stage == "ready":
        return JobSnapshot("completed", stage, current.retry_count)
    if stage == "queued":
        if current.stage != "queued":
            raise ValueError("A running job cannot return to queued")
        return JobSnapshot("queued", stage, current.retry_count)
    return JobSnapshot("processing", stage, current.retry_count)


def retry(current: JobSnapshot) -> JobSnapshot:
    if current.stage in TERMINAL:
        raise ValueError("Cannot retry a terminal job")
    return JobSnapshot("retrying", "retrying", current.retry_count + 1)

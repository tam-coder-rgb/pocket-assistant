"""So khớp tên thuốc theo TỪNG TỪ (không dùng khớp mờ trên cả chuỗi).

Vì sao: khớp mờ cả chuỗi coi "thuốc chuột" giống "Enterobella thuốc bột uống" chỉ vì cùng chữ "thuốc".
Quy tắc: bỏ từ chung (thuốc, viên...) và đơn vị (mg...), mọi từ còn lại trong câu tìm đều phải khớp
một từ của tên thuốc; chịu sai chính tả nhẹ ở từ chữ, còn số phải khớp tuyệt đối.
"""
import re
from collections.abc import Iterable
from dataclasses import dataclass

from rapidfuzz import fuzz

from backend.core.config import settings
from backend.core.text_fold import fold

_PARTS = re.compile(r"[a-z]+|\d+")  # "500mg" -> "500", "mg"
_MIN_FUZZY_LEN = 3  # từ ngắn hơn phải khớp tuyệt đối


@dataclass(frozen=True)
class MatchScore:
    """So sánh được bằng tuple: điểm trung bình các từ, rồi tỉ lệ từ của tên được phủ."""

    similarity: float
    coverage: float

    def key(self) -> tuple[float, float]:
        return (self.similarity, self.coverage)


def tokens(text: str) -> list[str]:
    skip = set(settings.MEDICINE_GENERIC_WORDS) | set(settings.MEDICINE_UNIT_WORDS)
    return [t for t in _PARTS.findall(fold(text)) if t not in skip]


def _token_similarity(query: str, name: str) -> float:
    if query == name:
        return 100.0
    if query.isdigit() or name.isdigit() or min(len(query), len(name)) < _MIN_FUZZY_LEN:
        return 0.0
    return fuzz.ratio(query, name)


def score(query_tokens: list[str], name_tokens: list[str]) -> MatchScore | None:
    """None nếu có từ trong câu tìm không khớp từ nào của tên."""
    if not query_tokens or not name_tokens:
        return None
    total, used = 0.0, set()
    for q in query_tokens:
        best_i, best = max(
            enumerate(_token_similarity(q, n) for n in name_tokens), key=lambda p: p[1]
        )
        if best < settings.RAPIDFUZZ_THRESHOLD:
            return None
        total += best
        used.add(best_i)
    return MatchScore(total / len(query_tokens), len(used) / len(name_tokens))


def pick_best(query: str, candidates: Iterable[tuple[int, str, bool]]) -> int | None:
    """candidates = (mã thuốc, tên/biệt danh, là tên chính). Trả mã thuốc khớp rõ ràng nhất.

    Hai thuốc KHÁC nhau ngang điểm (vd. "Hapacol" có nhiều hàm lượng) -> None, không đoán bừa.
    """
    q = tokens(query)
    best: dict[int, tuple[float, float, bool]] = {}
    for med_id, name, primary in candidates:
        if (s := score(q, tokens(name))) is not None:
            best[med_id] = max(best.get(med_id, (0, 0, False)), (*s.key(), primary))
    if not best:
        return None
    ranked = sorted(best.items(), key=lambda kv: kv[1], reverse=True)  # điểm, độ phủ, ưu tiên tên chính
    if len(ranked) > 1:
        (_, top), (_, runner_up) = ranked[0], ranked[1]
        same_score = top[:2] == runner_up[:2]
        if same_score and not (top[2] and not runner_up[2]):
            return None
    return ranked[0][0]

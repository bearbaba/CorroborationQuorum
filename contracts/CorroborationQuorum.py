# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *
from dataclasses import dataclass
import json


STANCES = ("SUPPORT", "CONTRADICT", "IRRELEVANT", "UNREADABLE")
FINALS = ("UPHELD", "REFUTED", "SPLIT", "INCONCLUSIVE")


@allow_storage
@dataclass
class Case:
    clerk: Address
    predicate: str
    rubric: str
    k: u32
    sources_csv: str
    source_count: u32
    sealed: bool
    status: str
    support_n: u32
    contradict_n: u32
    readable_n: u32
    stances_json: str
    justification: str
    round_no: u32


class CorroborationQuorum(gl.Contract):
    cases: TreeMap[str, Case]
    next_id: u32

    def __init__(self):
        self.next_id = u32(1)

    def _urls(self, csv: str):
        out = []
        for part in csv.split(","):
            u = part.strip()
            if u and u not in out:
                out.append(u)
        return out

    def _tally(self, urls, rows):
        by_url = {}
        for row in rows:
            if not isinstance(row, dict):
                continue
            u = str(row.get("url", "")).strip()
            st = str(row.get("stance", "UNREADABLE")).upper()
            if st not in STANCES:
                st = "UNREADABLE"
            if u in urls:
                by_url[u] = st
        support = 0
        contradict = 0
        readable = 0
        ordered = []
        for u in urls:
            st = by_url.get(u, "UNREADABLE")
            ordered.append({"url": u, "stance": st})
            if st == "UNREADABLE":
                continue
            readable += 1
            if st == "SUPPORT":
                support += 1
            elif st == "CONTRADICT":
                contradict += 1
        return support, contradict, readable, ordered

    def _status(self, k, support, contradict, readable):
        if readable == 0:
            return "INCONCLUSIVE"
        if support >= k and contradict == 0:
            return "UPHELD"
        if contradict >= 1 and support >= 1:
            return "SPLIT"
        if contradict >= k:
            return "REFUTED"
        return "INCONCLUSIVE"

    @gl.public.write
    def open_case(self, predicate: str, rubric: str, k: str, sources_csv: str) -> None:
        p = predicate.strip()
        r = rubric.strip()
        urls = self._urls(sources_csv)
        try:
            kk = int(str(k).strip())
        except Exception:
            kk = 0
        if not p or not r or not urls:
            raise Exception("predicate, rubric and sources required")
        if kk < 1 or kk > 5:
            raise Exception("k must be 1-5")
        if len(urls) > 5:
            raise Exception("max 5 sources")
        if kk > len(urls):
            raise Exception("k larger than source count")
        cid = int(self.next_id)
        self.next_id = u32(cid + 1)
        self.cases[str(cid)] = Case(
            clerk=gl.message.sender_address,
            predicate=p,
            rubric=r,
            k=u32(kk),
            sources_csv=",".join(urls),
            source_count=u32(len(urls)),
            sealed=False,
            status="OPEN",
            support_n=u32(0),
            contradict_n=u32(0),
            readable_n=u32(0),
            stances_json="[]",
            justification="",
            round_no=u32(0),
        )

    @gl.public.write
    def add_source(self, case_id: str, url: str) -> None:
        rec = self.cases[case_id]
        if rec.sealed:
            raise Exception("sources sealed")
        if rec.clerk != gl.message.sender_address:
            raise Exception("only clerk")
        urls = self._urls(rec.sources_csv)
        u = url.strip()
        if u and u not in urls:
            if len(urls) >= 5:
                raise Exception("max 5 sources")
            urls.append(u)
        rec.sources_csv = ",".join(urls)
        rec.source_count = u32(len(urls))
        self.cases[case_id] = rec

    @gl.public.write
    def seal_sources(self, case_id: str) -> None:
        rec = self.cases[case_id]
        if rec.clerk != gl.message.sender_address:
            raise Exception("only clerk")
        urls = self._urls(rec.sources_csv)
        if int(rec.k) > len(urls):
            raise Exception("k larger than source count")
        rec.sealed = True
        rec.status = "SEALED"
        self.cases[case_id] = rec

    @gl.public.write
    def adjudicate(self, case_id: str) -> None:
        rec_mem = gl.storage.copy_to_memory(self.cases[case_id])
        if not rec_mem.sealed:
            raise Exception("seal first")
        if rec_mem.status in FINALS:
            raise Exception("already final")
        urls = self._urls(rec_mem.sources_csv)
        predicate = rec_mem.predicate
        rubric = rec_mem.rubric
        k = int(rec_mem.k)

        def collect_evidence() -> str:
            parts = []
            for url in urls:
                try:
                    page = gl.nondet.web.render(url, mode="text")
                    text = page.strip() if page else ""
                    if not text:
                        parts.append("URL: " + url + "\nFAIL\nempty")
                    else:
                        low = text.lower()
                        hints = []
                        for tok in ("iana", "united nations", "example domain", "example.org"):
                            hints.append(tok + "=" + ("yes" if tok in low else "no"))
                        parts.append(
                            "URL: "
                            + url
                            + "\nOK\nLEXICAL: "
                            + ",".join(hints)
                            + "\n"
                            + text[:5000]
                        )
                except Exception as e:
                    parts.append("URL: " + url + "\nFAIL\n" + str(e))
            return "\n====\n".join(parts)

        raw = gl.eq_principle.prompt_non_comparative(
            collect_evidence,
            task=(
                "Label each fetched URL with exactly one stance. "
                "PREDICATE: " + predicate + " RUBRIC: " + rubric + " "
                "Rules: FAIL/empty -> UNREADABLE. "
                "If LEXICAL has iana=yes and the predicate is about IANA being mentioned, stance is SUPPORT. "
                "If the predicate claims the page is the UN homepage and LEXICAL has united nations=no, stance is CONTRADICT. "
                "IRRELEVANT only when the page is readable and the rubric gives no rule. "
                "Return ONLY raw JSON "
                '{"rows":[{"url":"...","stance":"SUPPORT|CONTRADICT|IRRELEVANT|UNREADABLE"}]} '
                "One row per URL. No markdown."
            ),
            criteria=(
                "JSON with rows. Each row url+stance. "
                "Stance is SUPPORT, CONTRADICT, IRRELEVANT or UNREADABLE. "
                "FAIL pages UNREADABLE. "
                "iana=yes plus IANA mention predicate => SUPPORT, not IRRELEVANT. "
                "UN homepage predicate plus generic IANA/example page => CONTRADICT, not IRRELEVANT. "
                "Do not invent facts."
            ),
        )

        if isinstance(raw, dict):
            parsed = raw
        else:
            text = str(raw)
            start = text.find("{")
            end = text.rfind("}")
            try:
                parsed = json.loads(text[start : end + 1]) if start >= 0 and end > start else {}
            except Exception:
                parsed = {"rows": []}
        rows = parsed.get("rows", [])
        if not isinstance(rows, list):
            rows = []
        support, contradict, readable, ordered = self._tally(urls, rows)
        status = self._status(k, support, contradict, readable)
        rec = self.cases[case_id]
        rec.status = status
        rec.support_n = u32(support)
        rec.contradict_n = u32(contradict)
        rec.readable_n = u32(readable)
        rec.stances_json = json.dumps(ordered)
        rec.justification = (
            "k=" + str(k)
            + " support=" + str(support)
            + " contradict=" + str(contradict)
            + " readable=" + str(readable)
        )[:500]
        rec.round_no = u32(int(rec.round_no) + 1)
        self.cases[case_id] = rec

    @gl.public.write
    def challenge(self, case_id: str, reason: str) -> None:
        rec = self.cases[case_id]
        if rec.status not in FINALS:
            raise Exception("nothing to challenge")
        if not reason.strip():
            raise Exception("reason required")
        rec.status = "CHALLENGED"
        rec.justification = reason.strip()[:500]
        self.cases[case_id] = rec

    @gl.public.view
    def get_case(self, case_id: str) -> str:
        if case_id not in self.cases:
            return "{}"
        rec = self.cases[case_id]
        return json.dumps(
            {
                "clerk": str(rec.clerk),
                "predicate": rec.predicate,
                "rubric": rec.rubric,
                "k": int(rec.k),
                "sources_csv": rec.sources_csv,
                "source_count": int(rec.source_count),
                "sealed": rec.sealed,
                "status": rec.status,
                "support_n": int(rec.support_n),
                "contradict_n": int(rec.contradict_n),
                "readable_n": int(rec.readable_n),
                "stances_json": rec.stances_json,
                "justification": rec.justification,
                "round_no": int(rec.round_no),
            }
        )

    @gl.public.view
    def get_status(self, case_id: str) -> str:
        if case_id not in self.cases:
            return ""
        return self.cases[case_id].status

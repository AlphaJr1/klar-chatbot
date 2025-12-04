import os, json, requests
from typing import Optional, Dict, Any

class OllamaClient:
    def __init__(
        self,
        host: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> None:
        self.host = (host or os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")).rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL", "qwen3:4B-instruct")
        self.timeout = float(timeout or os.getenv("OLLAMA_TIMEOUT", "60"))

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.host}{path}"
        try:
            r = requests.post(url, json=payload, timeout=self.timeout)
            r.raise_for_status()
            return r.json()
        except requests.RequestException:
            return {"response": ""}

    def generate(self, system: str, prompt: str, temperature: float = 0.2) -> str:
        text = f"<|system|>\n{system}\n<|user|>\n{prompt}\n<|assistant|>\n"
        payload = {
            "model": self.model,
            "prompt": text,
            "options": {"temperature": temperature},
            "stream": False,
        }
        try:
            out = self._post("/api/generate", payload)
            return (out.get("response") or "").strip()
        except requests.RequestException:
            return ""

    def generate_json(self, system: str, prompt: str, temperature: float = 0.0) -> Dict[str, Any]:
        sys = (
            "You are a strict JSON generator. Reply ONLY valid minified JSON without any prose. "
            "Do not include markdown, backticks, or explanations."
        )
        system2 = f"{sys}\n\n{system}".strip()
        text = self.generate(system=system2, prompt=prompt, temperature=temperature)
        try:
            return json.loads(text)
        except Exception:
            import re
            m = re.search(r"\{.*\}", text, flags=re.S)
            if m:
                try:
                    return json.loads(m.group(0))
                except Exception:
                    pass
            return {}
        


    def ok(self) -> bool:
        out = self.generate(system="You just answer OK.", prompt="Say OK once.", temperature=0.0)
        return bool(out)
import os, json, requests, time, asyncio, functools
from typing import Optional, Dict, Any

class OllamaClient:
    def __init__(
        self,
        host: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> None:
        env_host = os.getenv("OLLAMA_URL") or os.getenv("OLLAMA_BASE") or os.getenv("OLLAMA_HOST")
        if host:
            resolved_host = host
        elif env_host:
            resolved_host = env_host
        else:
            resolved_host = "http://127.0.0.1:11434"
        self.host = resolved_host.rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct")
        self.timeout = float(timeout or os.getenv("OLLAMA_TIMEOUT", "60"))
        self.retries = 3

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.host}{path}"
        for attempt in range(self.retries + 1):
            try:
                r = requests.post(url, json=payload, timeout=self.timeout)
                r.raise_for_status()
                return r.json()
            except requests.RequestException as e:
                if attempt < self.retries:
                    print (f"url: {url}")
                    print (f"path: {path}")
                    print(f"[OllamaClient] ⚠️ Attempt {attempt+1}/{self.retries+1} failed: {e}. Retrying in 5s...")
                    time.sleep(5)
                    continue
                print(f"[OllamaClient] ❌ Request failed after {self.retries+1} attempts: {e}")
                backup = os.getenv("OLLAMA_FALLBACK_HOST")
                if backup:
                    try:
                        r = requests.post(f"{backup}{path}", json=payload, timeout=self.timeout)
                        r.raise_for_status()
                        return r.json()
                    except Exception as e2:
                        print(f"[OllamaClient] Fallback failed: {e2}")
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
        
    # ASYNC VARIANTS
    async def async_generate(self, system: str, prompt: str, temperature: float = 0.2) -> str:
        loop = asyncio.get_event_loop()
        func = functools.partial(self.generate, system=system, prompt=prompt, temperature=temperature)
        return await loop.run_in_executor(None, func)

    async def async_generate_json(self, system: str, prompt: str, temperature: float = 0.0) -> Dict[str, Any]:
        loop = asyncio.get_event_loop()
        func = functools.partial(self.generate_json, system=system, prompt=prompt, temperature=temperature)
        return await loop.run_in_executor(None, func)

    def ok(self) -> bool:
        out = self.generate(system="You just answer OK.", prompt="Say OK once.", temperature=0.0)
        return bool(out)
    

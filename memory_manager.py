
import json
from pathlib import Path
from datetime import datetime

class MemoryManager:
    def __init__(self, path: str = "session_data.json"):
        self.path = Path(path)
        self.data = {
            "noticias": [],
            "ultimo_comando": "",
            "historico": [],
            "favoritos": [],
            "macros": {}
        }
        self._load()

    def _load(self):
        if self.path.exists():
            try:
                self.data = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                pass

    def save(self):
        try:
            self.path.write_text(
                json.dumps(self.data, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
        except Exception:
            pass

    def set_noticias(self, noticias_list):
        self.data["noticias"] = noticias_list[:300]
        self.save()

    def get_noticias(self):
        return self.data.get("noticias", [])

    def toggle_favorito(self, item):
        favs = self.data.get("favoritos", [])
        if item in favs:
            favs.remove(item)
        else:
            favs.append(item)
        self.data["favoritos"] = favs[:200]
        self.save()

    def get_favoritos(self):
        return self.data.get("favoritos", [])

    def set_ultimo(self, comando: str):
        self.data["ultimo_comando"] = comando
        self.data["historico"].append({
            "ts": datetime.now().strftime("%H:%M:%S"),
            "cmd": comando
        })
        self.data["historico"] = self.data["historico"][-50:]
        self.save()

    def get_ultimo(self):
        return self.data.get("ultimo_comando", "")

    def get_historico(self):
        return self.data.get("historico", [])

    def salvar_macro(self, nome: str, comandos: list):
        self.data["macros"][nome] = comandos
        self.save()

    def listar_macros(self):
        return list(self.data.get("macros", {}).keys())

    def obter_macro(self, nome: str):
        return self.data.get("macros", {}).get(nome, [])

    def exportar(self, formato: str = "json", base_dir: str = "exports", somente_favoritos: bool=False, filtro: str=""):
        from pathlib import Path
        base = Path(base_dir); base.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%d_%Hh%M")

        noticias = self.get_favoritos() if somente_favoritos else self.get_noticias()
        if filtro:
            noticias = [n for n in noticias if filtro.lower() in n.get("titulo","").lower()]

        if formato.lower() == "json":
            p = base / f"noticias_{ts}.json"
            p.write_text(json.dumps(noticias, ensure_ascii=False, indent=2), encoding="utf-8")
            return str(p)
        elif formato.lower() == "csv":
            import pandas as pd
            p = base / f"noticias_{ts}.csv"
            pd.DataFrame(noticias).to_csv(p, index=False, encoding="utf-8-sig")
            return str(p)
        elif formato.lower() == "txt":
            p = base / f"noticias_{ts}.txt"
            with p.open("w", encoding="utf-8") as f:
                for i, n in enumerate(noticias, 1):
                    f.write(f"{i}. {n.get('titulo','')} - {n.get('link','')}")
                
            return str(p)
        elif formato.lower() == "xlsx":
            import pandas as pd
            p = base / f"noticias_{ts}.xlsx"
            pd.DataFrame(noticias).to_excel(p, index=False)
            return str(p)
        elif formato.lower() == "html":
            p = base / f"noticias_{ts}.html"
            html = "<html><body><h1>Notícias</h1><ul>"
            for n in noticias:
                html += f"<li><a href='{n.get('link','')}' target='_blank'>{n.get('titulo','')}</a></li>"
            html += "</ul></body></html>"
            p.write_text(html, encoding="utf-8")
            return str(p)
        else:
            raise ValueError("Formato não suportado. Use json, csv, txt, xlsx ou html.")

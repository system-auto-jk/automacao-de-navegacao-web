
import google.generativeai as genai
import json, unicodedata, re

def _carregar_api_key():
    try:
        return json.loads(open("config.json","r",encoding="utf-8").read()).get("GEMINI_API_KEY")
    except Exception:
        return None

def _norm(s: str) -> str:
    if not s: return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower().strip()

genai.configure(api_key=_carregar_api_key())

def conversar_ia(prompt: str) -> str:
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        system = "Responda de forma clara, objetiva e formatada. Use listas quando fizer sentido."
        r = model.generate_content(system + "\n\n" + prompt)
        return (getattr(r, "text", "") or "").strip()
    except Exception as e:
        return f"❌ Erro IA: {e}"

def interpretar_comando(comando_usuario: str, contexto_pagina: str = "") -> dict:
    raw = comando_usuario.strip()
    t = _norm(raw)

    if (t.startswith("http") or ".com" in t or "www." in t) and not t.startswith(("clicar","digitar","escrever","preencher","insira","coloque","abrir ")):
        url = raw if raw.startswith("http") else ("https://" + raw)
        return {"acao": "abrir_url", "valor": url}

    if any(k in t for k in ["abrir ", "abra "]):
        m = re.sub(r"^(abrir|abra)\s+", "", raw, flags=re.IGNORECASE).strip()
        if m:
            if not m.startswith("http"): m = "https://" + m
            return {"acao": "abrir_url", "valor": m}

    if "voltar" in t: return {"acao":"voltar"}
    if "avancar" in t or "avançar" in t: return {"acao":"avancar"}
    if "recarregar" in t or "atualizar pagina" in t or "atualizar página" in t: return {"acao":"recarregar"}
    if "nova aba" in t or "abrir nova aba" in t: return {"acao":"nova_aba"}
    if "fechar aba" in t: return {"acao":"fechar_aba"}

    if any(k in t for k in ["role", "rolar", "descer", "para baixo"]): return {"acao":"rolar","valor":"down"}
    if any(k in t for k in ["suba","rolar para cima","para cima","subir"]): return {"acao":"rolar","valor":"up"}

    def montar_localizador(frase: str):
        m = re.search(r'(?:no|em)\s*xpath\s+(.+)$', frase, re.IGNORECASE)
        if m: return {"tipo":"xpath", "valor": m.group(1).strip()}
        m = re.search(r'(?:no|em)\s*id\s+([\w\-\:\.\[\]@]+)', frase, re.IGNORECASE)
        if m: return {"tipo":"id", "valor": m.group(1).strip()}
        m = re.search(r'(?:no|em)\s*name\s+([\w\-\:\.\[\]@]+)', frase, re.IGNORECASE)
        if m: return {"tipo":"name", "valor": m.group(1).strip()}
        q = re.findall(r'"(.*?)"', frase)
        if q and ("no campo" in _norm(frase) or "no elemento" in _norm(frase) or "no elementor" in _norm(frase)):
            alvo = q[-1]; return {"tipo":"texto", "valor": alvo}
        m = re.search(r'(?:no|em)\s+(campo|elemento|elementor|login|busca|pesquisa|email|senha|usuario|usuário|nome)\b', frase, re.IGNORECASE)
        if m: return {"tipo":"texto", "valor": m.group(1).strip()}
        if q: return {"tipo":"texto", "valor": q[0]}
        return None

    # Versão estendida: aceita css, class, type/tipo, placeholder, aria-label
    def montar_localizador2(frase: str):
        m = re.search(r'(?:no|em)\s*css\s+(.+)$', frase, re.IGNORECASE)
        if m:
            return {"tipo": "css", "valor": m.group(1).strip()}
        m = re.search(r'(?:no|em)\s*xpath\s+(.+)$', frase, re.IGNORECASE)
        if m:
            return {"tipo": "xpath", "valor": m.group(1).strip()}
        m = re.search(r'(?:no|em)\s*id\s+([\w\-\:\.\[\]@]+)', frase, re.IGNORECASE)
        if m:
            return {"tipo": "id", "valor": m.group(1).strip()}
        m = re.search(r'(?:no|em)\s*name\s+([\w\-\:\.\[\]@]+)', frase, re.IGNORECASE)
        if m:
            return {"tipo": "name", "valor": m.group(1).strip()}
        m = re.search(r'(?:no|em)\s*(?:class|classe)\s+(?:\"([^\"]+)\"|(\S+))', frase, re.IGNORECASE)
        if m:
            val = (m.group(1) or m.group(2) or '').strip()
            return {"tipo": "class", "valor": val}
        m = re.search(r'(?:no|em)\s*(?:type|tipo)\s+(\S+)', frase, re.IGNORECASE)
        if m:
            return {"tipo": "type", "valor": m.group(1).strip()}
        m = re.search(r'(?:no|em)\s*placeholder\s+(?:\"([^\"]+)\"|(\S+))', frase, re.IGNORECASE)
        if m:
            val = (m.group(1) or m.group(2) or '').strip()
            return {"tipo": "placeholder", "valor": val}
        m = re.search(r'(?:no|em)\s*aria[\-\s]*label\s+(?:\"([^\"]+)\"|(\S+))', frase, re.IGNORECASE)
        if m:
            val = (m.group(1) or m.group(2) or '').strip()
            return {"tipo": "aria-label", "valor": val}
        # fallback: usa a versão antiga
        return montar_localizador(frase)

    if t.startswith("clicar") or t.startswith("clique"):
        loc = montar_localizador2(raw)
        if loc:
            return {"acao":"clicar","localizador":loc}
        return {"acao":"clicar","localizador":{"tipo":"texto","valor":raw.replace("clicar","").replace("clique","").strip()}}

    if any(k in t for k in ["digite","escreva","preencha","insira","coloque","digitar","escrever"]):
        # Captura texto a ser digitado ANTES do localizador para evitar pegar quotes do XPath (ex.: id="loginForm").
        # 1) Identifica posição do localizador (no|em xpath/id/name/campo/elemento)
        mloc = re.search(r"\b(?:no|em)\s+(xpath|id|name|campo|elemento)\b", raw, flags=re.IGNORECASE)
        pre = raw[:mloc.start()] if mloc else raw
        # 2) Tenta pegar texto entre aspas no trecho anterior ao localizador
        qpre = re.findall(r'"(.*?)"', pre)
        if qpre:
            texto = qpre[0]
        else:
            # 3) Sem aspas: remove o verbo e usa o restante como texto
            resto = re.sub(r"^(digite|escreva|preencha|insira|coloque|digitar|escrever)\s+", "", pre, flags=re.IGNORECASE).strip()
            texto = resto
        loc = montar_localizador2(raw)
        return {"acao":"digitar","texto":texto,"localizador":loc}

    if "enter" in t: return {"acao":"enter"}

    if any(p in t for p in ["fechar pop", "fechar janela", "fechar aviso", "fechar propaganda", "fechar anúncio", "fechar anuncio"]):
        return {"acao":"fechar_popup"}

    if any(p in t for p in ["pegue as noticias","pegue as notícias","extrair noticias","extrair notícias","pegar noticias"]):
        return {"acao":"extrair_noticias"}
    if "extrair links" in t: return {"acao":"extrair_links"}
    if "extrair imagens" in t: return {"acao":"extrair_imagens"}
    if "extrair tabelas" in t: return {"acao":"extrair_tabelas"}
    if "salvar html" in t: return {"acao":"salvar_html"}

    if any(p in t for p in ["listar","liste","mostrar","mostre"]) and ("notic" in t or "manchete" in t):
        return {"acao":"listar_memoria","formato":raw}
    if "exporte" in t or "exportar" in t:
        formato = "json"
        if "csv" in t: formato="csv"
        elif "txt" in t: formato="txt"
        elif "xlsx" in t: formato="xlsx"
        elif "html" in t: formato="html"
        somente_fav = "favorit" in t
        q = re.findall(r'"(.*?)"', raw)
        filtro = q[-1] if q else ""
        return {"acao":"exportar","formato":formato, "somente_favoritos": somente_fav, "filtro": filtro}

    if any(p in t for p in ["print","screenshot","captura de tela","tire print"]): return {"acao":"screenshot"}
    if "repetir" in t and "ultimo" in t: return {"acao":"repetir_ultimo"}
    if "limpar" in t: return {"acao":"limpar"}
    if "funcoes" in t or "funções" in t or "ajuda" in t: return {"acao":"help"}
    if "sair" in t or "encerrar" in t: return {"acao":"sair"}

    if any(p in t for p in ["resuma","resumo","explique","interprete","traduza","tradução","resumo em markdown"]):
        return {"acao":"resumir","pedido": raw}

    if "criar macro" in t:
        nome = "macro"
        q = re.findall(r'"(.*?)"', raw)
        if q: nome = q[0]
        return {"acao":"criar_macro","nome": nome}
    if any(p in t for p in ["parar macro","pare macro","finalizar macro","encerrar macro","stop macro"]):
        return {"acao":"parar_macro"}
    if "rodar macro" in t or "executar macro" in t:
        q = re.findall(r'"(.*?)"', raw)
        if q: return {"acao":"rodar_macro","nome": q[0]}
        return {"acao":"rodar_macro","nome": ""}
    if "listar macros" in t:
        return {"acao":"listar_macros"}

    return {"acao":"desconhecida"}

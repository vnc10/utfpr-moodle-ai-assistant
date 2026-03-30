# UTFPR Moodle AI Assistant

Ferramenta de linha de comando para professores da UTFPR que automatiza o download de materiais e submissões do Moodle, com correção automática de atividades e geração de roteiros de aula usando a API do Google Gemini.

## Funcionalidades principais

- **Autenticação** no Moodle da UTFPR via username/RA e senha.
- **Menu interativo** com três opções: download de materiais, correção de exercícios e geração de roteiros de aula.
- **Download de materiais** do curso (PDFs, slides do Google Docs/Slides, documentos).
- **Correção automática com IA** (Gemini), gerando feedback em HTML com nota 10.
- **Upload de slides do professor** como contexto para a IA gerar feedbacks mais precisos.
- **Geração de roteiros de aula** (Lesson Plans) a partir dos slides em PDF, exportados como `.docx`.
- **Continuidade entre aulas** — roteiros anteriores são lidos automaticamente para manter a progressão lógica do conteúdo.
- **Retry automático** em caso de erro de quota da API do Gemini.
- **Navegação entre disciplinas** sem precisar reabrir o programa.

## Pré-requisitos

- Python 3.9+
- Conta de professor no Moodle da UTFPR.
- Chave de API do Google Gemini (configurada em `config.py` ou via variável de ambiente `GOOGLE_API_KEY`).

## Instalação

```bash
# Clone o repositório
git clone <url-do-repositorio>
cd utfpr-moodle-ai-assistant

# Crie o ambiente virtual
python3 -m venv venv

# Ative o ambiente virtual
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows

# Instale as dependências
pip install google-genai python-docx
```

## Como usar

```bash
# Ative o venv (sempre antes de rodar)
source venv/bin/activate

# Execute
python main.py
```

O programa irá:

1. Pedir seu **username/RA** e **senha** do Moodle.
2. Listar suas **disciplinas** disponíveis.
3. Exibir o **menu de ações**:
   - `[0]` **Download de materiais** — baixa PDFs, slides e documentos da disciplina.
   - `[1]` **Correção de listas de exercícios** — baixa submissões dos alunos e, opcionalmente, corrige com IA (nota 10) e envia feedback em HTML.
   - `[2]` **Geração de roteiro de aula** — seleciona um slide em PDF, gera um roteiro detalhado com IA e salva como `.docx` na pasta `Roteiros/`.
4. Processar a ação selecionada automaticamente.
5. Ao finalizar, perguntar se deseja voltar ao menu de disciplinas.

## Estrutura de pastas gerada

Ao rodar o programa, ele cria pastas seguindo a estrutura do Moodle:

```
Nome_da_Disciplina/
├── Secao_1/
│   ├── Material_Aula1.pdf
│   ├── Slides_Aula1.pdf
│   └── Submissions_Nome_da_Atividade/
│       ├── Student_12345/
│       │   ├── trabalho.py
│       │   └── relatorio.pdf
│       └── Student_67890/
│           └── codigo.c
├── Secao_2/
│   ├── Material_Aula2.pdf
│   └── Submissions_Outra_Atividade/
│       └── ...
├── Roteiros/
│   ├── Roteiro_Aula_01.docx
│   ├── Roteiro_Aula_02.docx
│   └── ...
└── ...
```

- Cada **seção** do Moodle vira uma pasta.
- **Materiais** (PDFs, slides) são salvos dentro da seção correspondente.
- **Submissões** ficam em pastas `Submissions_<nome_atividade>`, separadas por aluno (`Student_<id>`).
- Arquivos binários (`.exe`, `.o`, `.out`, `.bin`, `.pyc`) são ignorados automaticamente.
- Arquivos `.zip` enviados por alunos são extraídos automaticamente.
- **Roteiros de aula** gerados pela IA são salvos na pasta `Roteiros/` com numeração sequencial.

## Geração de roteiros de aula

A opção **Gerar roteiro de aula** permite criar um roteiro detalhado a partir de um slide em PDF da disciplina. O processo:

1. Lista os PDFs disponíveis nas pastas de slides do curso.
2. O professor seleciona o slide desejado.
3. O slide é enviado ao Gemini (modelo `gemini-3.1-pro-preview`) junto com roteiros anteriores para manter continuidade.
4. O roteiro gerado é convertido de Markdown para `.docx` (Word) e salvo na pasta `Roteiros/`.

Cada roteiro inclui, para cada slide: tempo estimado, roteiro de fala detalhado, foco visual e sugestões de interação com a turma.

## Contexto da IA (slides do professor)

Quando a opção de enviar slides como contexto está ativa, o programa busca PDFs dentro de pastas específicas do curso para enviar ao Gemini. Isso permite que o feedback use a mesma terminologia das aulas.

**Pastas padrão escaneadas:** `Slides` e `Atividades`.

Isso pode ser customizado por disciplina no arquivo `config.py`, através do dicionário `TEACHER_FOLDERS_BY_COURSE`.

## Estrutura do projeto

| Arquivo | Descrição |
|---|---|
| `main.py` | Ponto de entrada, fluxo principal e menu interativo. |
| `config.py` | Configurações (API keys, URLs, extensões, pastas de contexto). |
| `moodle_api.py` | Comunicação com a API REST do Moodle (auth, cursos, submissões, notas). |
| `downloader.py` | Download de materiais e submissões (inclui suporte a Google Docs/Slides). |
| `gemini_ai.py` | Integração com o Gemini (upload, geração de feedback, roteiros de aula, conversão para `.docx`). |
| `grader.py` | Orquestração da correção: download, avaliação por IA e envio de nota. |

## Configuração

As principais configurações ficam em `config.py`:

- `GEMINI_API_KEY` — Chave da API do Google Gemini.
- `GEMINI_MODEL` — Modelo do Gemini para correção (padrão: `gemini-2.5-flash-lite`).
- `GEMINI_MODEL_PRO` — Modelo do Gemini para geração de roteiros (padrão: `gemini-3.1-pro-preview`).
- `BASE_URL` — URL base do Moodle (`https://moodle.utfpr.edu.br`).
- `FORBIDDEN_EXTENSIONS` — Extensões de arquivo ignoradas no download.
- `TEXT_CODE_EXTENSIONS` — Extensões lidas como texto para a IA.
- `MEDIA_EXTENSIONS` — Extensões enviadas via upload para o Gemini.
- `TEACHER_FOLDERS_DEFAULT` — Pastas padrão para contexto do professor.
- `TEACHER_FOLDERS_BY_COURSE` — Mapeamento customizado de pastas por disciplina.
- `MAX_RETRIES` / `RETRY_DELAY_SECONDS` — Configuração de retry para erros de quota.

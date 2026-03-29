# UTFPR Moodle AI Assistant

Ferramenta de linha de comando para professores da UTFPR que automatiza o download de materiais e submissoes do Moodle, com correcao automatica de atividades usando a API do Google Gemini.

## Funcionalidades

- **Autenticacao** no Moodle da UTFPR via username/RA e senha
- **Download de materiais** do curso (PDFs, slides do Google Docs/Slides, documentos)
- **Download de submissoes** dos alunos por atividade
- **Correcao automatica com IA** (Gemini) gerando feedback em HTML com nota 10
- **Upload de slides do professor** como contexto para a IA gerar feedbacks mais precisos
- **Retry automatico** em caso de erro de quota da API do Gemini
- **Navegacao entre disciplinas** sem precisar reabrir o programa

## Pre-requisitos

- Python 3.9+
- Conta de professor no Moodle da UTFPR
- Chave de API do Google Gemini (configurada em `config.py` ou via variavel de ambiente `GOOGLE_API_KEY`)

## Instalacao

```bash
# Clone o repositorio
git clone <url-do-repositorio>
cd utfpr-moodle-ai-assistant

# Crie o ambiente virtual
python3 -m venv venv

# Ative o ambiente virtual
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows

# Instale as dependencias
pip install google-genai
```

## Como usar

```bash
# Ative o venv (sempre antes de rodar)
source venv/bin/activate

# Execute
python main.py
```

O programa ira:

1. Pedir seu **username/RA** e **senha** do Moodle
2. Listar suas **disciplinas** disponiveis
3. Perguntar o que deseja fazer:
   - Baixar materiais da disciplina
   - Baixar submissoes dos alunos
   - Usar IA para corrigir (opcional)
   - Enviar slides como contexto para a IA (opcional)
4. Processar tudo automaticamente
5. Ao finalizar, perguntar se deseja voltar ao menu de disciplinas

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
└── ...
```

- Cada **secao** do Moodle vira uma pasta
- **Materiais** (PDFs, slides) sao salvos dentro da secao correspondente
- **Submissoes** ficam em pastas `Submissions_<nome_atividade>`, separadas por aluno (`Student_<id>`)
- Arquivos binarios (`.exe`, `.o`, `.out`, `.bin`, `.pyc`) sao ignorados automaticamente
- Arquivos `.zip` enviados por alunos sao extraidos automaticamente

## Contexto da IA (slides do professor)

Quando a opcao de enviar slides como contexto esta ativa, o programa busca PDFs dentro de pastas especificas do curso para enviar ao Gemini. Isso permite que o feedback use a mesma terminologia das aulas.

**Pastas padrao escaneadas:** `Slides` e `Atividades`

Isso pode ser customizado por disciplina no arquivo `config.py` atraves do dicionario `TEACHER_FOLDERS_BY_COURSE`.

## Estrutura do projeto

| Arquivo | Descricao |
|---|---|
| `main.py` | Ponto de entrada, fluxo principal e menu interativo |
| `config.py` | Configuracoes (API keys, URLs, extensoes, pastas de contexto) |
| `moodle_api.py` | Comunicacao com a API REST do Moodle (auth, cursos, submissoes, notas) |
| `downloader.py` | Download de materiais e submissoes (inclui suporte a Google Docs/Slides) |
| `gemini_ai.py` | Integracao com o Gemini (upload, geracao de feedback, gerenciamento de arquivos) |
| `grader.py` | Orquestracao da correcao: download, avaliacao por IA e envio de nota |

## Configuracao

As principais configuracoes ficam em `config.py`:

- `GEMINI_API_KEY` — chave da API do Google Gemini
- `GEMINI_MODEL` — modelo do Gemini utilizado (padrao: `gemini-2.5-flash-lite`)
- `BASE_URL` — URL base do Moodle (`https://moodle.utfpr.edu.br`)
- `FORBIDDEN_EXTENSIONS` — extensoes de arquivo ignoradas no download
- `TEXT_CODE_EXTENSIONS` — extensoes lidas como texto para a IA
- `MEDIA_EXTENSIONS` — extensoes enviadas via upload para o Gemini
- `TEACHER_FOLDERS_DEFAULT` — pastas padrao para contexto do professor
- `TEACHER_FOLDERS_BY_COURSE` — mapeamento customizado de pastas por disciplina
- `MAX_RETRIES` / `RETRY_DELAY_SECONDS` — configuracao de retry para erros de quota

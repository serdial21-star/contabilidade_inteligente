# Brand Color Specification

Fonte oficial: [identidade visual S21 v1.png](../ui/assets/brand/identidade%20visual%20S21%20v1.png), fornecida pelo usuário durante a Phase 02. BRAND_COLOR_VALUES = OFFICIAL para a paleta institucional abaixo. As cores de interface derivadas têm STATUS PROVISIONAL; não são uma nova identidade.

Mecanismo: CSS custom properties em [tokens.css](../ui/tokens.css), escopadas por `.foundation` para não modificar a prévia/site anteriores. Razões calculadas a partir de luminância sRGB, arredondadas a duas casas; aplicam-se às combinações indicadas, não certificam a página inteira.

| TOKEN | USE | CONTRAST | STATUS | VALUE |
| --- | --- | --- | --- | --- |
| `--brand-primary` | Operação, confiança, estrutura, ação primária | 13,96:1 sobre branco | OFFICIAL | `#17295B` |
| `--brand-gold` | Inteligência, detalhe premium, acento decorativo | 2,17:1 sobre branco; texto azul sobre ouro 6,44:1 | OFFICIAL | `#DAA84F` |
| `--brand-red` | Identidade “21”, marca | 5,01:1 sobre branco | OFFICIAL | `#D8232A` |
| `--surface` | Branco, superfícies principais | Texto azul 13,96:1 | OFFICIAL | `#FFFFFF` |
| `--background` | Cinza neutro, fundo do app | Usar texto azul/escuro | OFFICIAL | `#F3F4F6` |
| `--text` | Texto principal, alias funcional do azul | 13,96:1 sobre branco | PROVISIONAL | `#17295B` |
| `--text-secondary` | Descrições/legendas | 6,25:1 sobre branco | PROVISIONAL | `#566174` |
| `--border` | Separação decorativa de cards | Não depender desta linha para identificar controles | PROVISIONAL | `#DCE1E9` |
| `--control-border` | Limite de campos | 3,72:1 sobre branco | PROVISIONAL | `#7B8596` |
| `--success` / `--success-bg` | Aprovação humana/sucesso | 5,69:1 no fundo correspondente | PROVISIONAL | `#216C48` / `#EAF5EE` |
| `--warning` / `--warning-bg` | Atenção/revisão | 6,10:1 no fundo correspondente | PROVISIONAL | `#80520C` / `#FFF3DB` |
| `--danger` / `--danger-bg` | Bloqueio, erro, ação perigosa | 5,93:1 no fundo correspondente | PROVISIONAL | `#B51F2B` / `#FFF0EF` |
| `--info` / `--info-bg` | Processamento/informação/foco | 6,13:1 no fundo correspondente | PROVISIONAL | `#285D95` / `#EDF4FC` |
| `--intelligent` / `--intelligent-bg` | Texto “Sugestão inteligente” e fundo | 6,76:1 no fundo correspondente | PROVISIONAL | `#77500A` / `#FFF8E9` |
| `--neutral-bg` | Estado neutro | Usar texto secundário | PROVISIONAL | `#EEF0F3` |

O ouro oficial não é usado como texto pequeno sobre branco nem como único sinal de estado. Sugestão inteligente usa acento ouro, ícone e texto escuro. Aprovação humana usa verde e identifica ator/instante quando disponíveis. Vermelho institucional não vira ação primária normal; ações perigosas usam token danger e confirmação explícita.

As assinaturas PNG são oficiais como fornecidas. Variações de tonalidade dentro da imagem não substituem os hex escritos na prancha. Nenhuma extração de cor por pixel foi promovida a especificação institucional.

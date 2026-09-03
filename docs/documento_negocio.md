# QChat — Sistema de Mensageria Híbrida Resistente a Computadores Quânticos

## Documento de Negócio

---

## 1. Sumário Executivo

O QChat é uma aplicação experimental de mensageria segura desenvolvida como prova de conceito para investigar a viabilidade técnica de combinar **Distribuição de Chaves Quânticas (QKD)** e **Criptografia Pós-Quântica (PQC)** em um sistema de comunicação digital. A aplicação permite que dois usuários troquem mensagens privadas em tempo real com a chave de sessão estabelecida por um dentre quatro protocolos selecionáveis: BB84 (QKD puro), ML-KEM (PQC puro, padrão NIST FIPS 203), Híbrido (combinação dos dois) e RSA (criptografia clássica, usado como controle experimental).

O produto se posiciona no contexto da transição criptográfica iniciada com a padronização dos algoritmos pós-quânticos pelo NIST em agosto de 2024, oferecendo uma plataforma demonstrativa e mensurável das diferentes abordagens disponíveis para proteção contra a ameaça representada por computadores quânticos criptograficamente relevantes.

---

## 2. Contexto e Problema

### 2.1 A ameaça quântica

A segurança da comunicação digital contemporânea apoia-se majoritariamente em algoritmos de chave pública como RSA e ECDSA, cuja proteção depende da dificuldade computacional de problemas matemáticos clássicos (fatoração de inteiros e logaritmo discreto). O algoritmo de Shor demonstrou, em 1994, que computadores quânticos suficientemente capazes podem resolver esses problemas em tempo polinomial, comprometendo de forma generalizada a criptografia em uso.

Ainda que um computador quântico criptograficamente relevante não esteja disponível no presente, dois fatores tornam a ameaça atual:

- **Cronograma de migração**: substituir a pilha criptográfica de organizações inteiras é um processo de anos. Iniciar a transição apenas quando a ameaça se concretizar é tarde demais.
- **Modelo *harvest-now-decrypt-later***: adversários podem coletar tráfego cifrado hoje e armazená-lo para decifrar quando dispuserem da capacidade necessária. Dados com requisito de confidencialidade de longo prazo já estão expostos.

### 2.2 Duas linhas de resposta

A comunidade técnica desenvolveu duas linhas complementares para responder à ameaça:

**Criptografia Pós-Quântica (PQC)** — algoritmos clássicos cuja segurança não depende de problemas vulneráveis ao algoritmo de Shor. O NIST concluiu em agosto de 2024 a primeira rodada de padronização, publicando ML-KEM (FIPS 203) para encapsulamento de chaves, ML-DSA (FIPS 204) e SLH-DSA (FIPS 205) para assinaturas digitais. PQC opera sobre hardware convencional e é compatível com a infraestrutura existente.

**Distribuição de Chaves Quânticas (QKD)** — protocolos como BB84 que estabelecem chaves secretas usando estados quânticos. A segurança apoia-se em princípios da mecânica quântica (teorema da não-clonagem e perturbação por medição), oferecendo a propriedade teórica de segurança incondicional. Em contrapartida, QKD exige hardware dedicado, tem distância limitada sem repetidores quânticos e não resolve nativamente o problema de autenticação.

### 2.3 Lacuna investigada

O posicionamento atual de agências de segurança (NSA, NCSC britânico, ANSSI francês) é favorável a PQC como solução primária em larga escala, com QKD recomendada apenas para nichos específicos. A discussão acadêmica converge para esquemas híbridos que combinam ambas as abordagens, herdando vantagens e mitigando limitações. Apesar desse consenso emergente, a aplicação prática de esquemas híbridos a sistemas de mensageria de uso cotidiano permanece pouco explorada experimentalmente.

O QChat preenche essa lacuna por meio de uma implementação concreta, mensurável e reproduzível.

---

## 3. Propósito do Sistema

O QChat tem três propósitos articulados:

### 3.1 Propósito acadêmico

Servir como artefato experimental para o Trabalho de Conclusão de Curso, permitindo a coleta de dados empíricos sobre o comportamento de protocolos QKD, PQC, híbridos e clássicos em condições controladas, com adversário simulado de forma parametrizável.

### 3.2 Propósito demonstrativo

Tornar concretos e tangíveis conceitos que geralmente permanecem em literatura técnica especializada. A aplicação permite que avaliadores, estudantes e interessados interajam diretamente com sistemas que implementam QKD e PQC, observando em tempo real métricas como o QBER (Taxa de Erro Quântico de Bits) e o tempo de estabelecimento de chave em cada modo.

### 3.3 Propósito investigativo

Responder, com base em dados, à pergunta de pesquisa do TCC: *no contexto pós-padronização do NIST (2024), quais são as condições técnicas e os trade-offs envolvidos na implementação de um sistema de mensageria que combine BB84 e ML-KEM em esquema híbrido, comparado a abordagens isoladas, sob um modelo controlado de adversário?*

---

## 4. Público-alvo

O QChat **não é** destinado a uso comercial nem a substituir aplicativos de mensageria de produção. Seus públicos são:

- **Banca examinadora do TCC** — avaliará a aplicação durante a defesa, com acesso à URL pública para verificar de forma independente as funcionalidades descritas.
- **Pesquisadores e estudantes** de criptografia, segurança computacional ou computação quântica que queiram observar uma implementação concreta de pipeline QKD completo (incluindo *sifting*, estimativa de QBER, reconciliação Cascade e *privacy amplification*) integrado a ML-KEM.
- **Comitês de admissão** de programas de mestrado e doutorado no exterior, para os quais o trabalho serve como demonstração das capacidades técnicas e investigativas do autor.
- **Comunidade *open-source*** interessada em código de referência para experimentação com criptografia pós-quântica em aplicações reais.

---

## 5. Como Funciona

### 5.1 Visão geral do uso

Um usuário acessa o QChat pela web. Após cadastro com nome de usuário e senha, ele faz *login* e visualiza um *lobby* contendo outros usuários autenticados disponíveis. Ao selecionar um interlocutor, escolhe entre os quatro modos criptográficos disponíveis e solicita o início da sessão. Quando o outro usuário aceita, o sistema executa automaticamente o protocolo escolhido para estabelecer uma chave compartilhada, e a sessão de chat é iniciada. As mensagens trocadas são cifradas com a chave estabelecida; o usuário visualiza, ao lado da conversa, métricas técnicas relevantes, como o modo da sessão, o tempo gasto no estabelecimento e, no caso de modos baseados em QKD, o QBER medido. Ao encerrar a sessão, as chaves são descartadas e as mensagens não são preservadas.

### 5.2 Os quatro modos de operação

**BB84** — protocolo de QKD em sua forma operacional completa. Alice prepara qubits em bases aleatórias e os transmite a Bob via canal quântico simulado; Bob mede em bases também aleatórias; ambos comparam bases pelo canal clássico, descartam as discrepantes (*sifting*), estimam o QBER sobre uma amostra, executam reconciliação de erros pelo protocolo Cascade e aplicam amplificação de privacidade por *hashing* universal. A chave final destilada cifra as mensagens da sessão.

**ML-KEM** — implementação do padrão NIST FIPS 203. Bob gera um par de chaves; Alice usa a chave pública para encapsular uma chave compartilhada; Bob recupera a mesma chave via decapsulamento.

**Híbrido (BB84 + ML-KEM)** — executa os dois protocolos em paralelo e combina as chaves resultantes por meio da função de derivação HKDF. A chave final é segura enquanto pelo menos um dos protocolos componentes permanecer seguro, mitigando o risco de uma eventual quebra futura de qualquer das duas linhas isoladamente.

**RSA** — empregado como controle experimental. Permite comparar o desempenho das abordagens resistentes à computação quântica com o algoritmo clássico que elas se propõem a substituir.

### 5.3 Detecção de espionagem

Quando o protocolo BB84 ou o modo Híbrido está em uso, o sistema monitora continuamente o QBER da sessão. Se o valor medido exceder o limiar configurado, o sistema:

1. Encerra a sessão automaticamente.
2. Notifica visualmente ambos os usuários por meio de um alerta na interface.
3. Registra o evento em log estruturado.

Esse comportamento é a manifestação concreta da propriedade fundamental que distingue QKD de criptografia clássica: a capacidade de detectar tentativas de espionagem como consequência direta dos princípios da mecânica quântica.

### 5.4 Modelo de adversário simulado

Para fins experimentais, o sistema pode ser executado com um simulador de adversário (denominado *Eve* na convenção criptográfica) ativo no canal quântico. Três modos de ataque são suportados:

- **Passivo** — Eve não interfere.
- ***Intercept-resend*** — Eve intercepta cada qubit, mede em base aleatória e reenvia o resultado. Esse ataque introduz QBER próximo a 25%, valor detectável pelo monitoramento.
- ***Beam-splitting*** — Eve retém cópia de uma fração parametrizável dos qubits, simulando interceptação parcial.

O simulador de adversário é ativado exclusivamente por configuração administrativa e nunca está disponível em ambiente de produção pública. Sua finalidade é gerar dados experimentais para validar empiricamente a detectabilidade prevista teoricamente.

### 5.5 Decisões de design relevantes ao negócio

**Conversa um-para-um.** O QChat suporta apenas conversas privadas entre dois usuários. Conversas em grupo exigiriam protocolos de *group key agreement* que estão fora do escopo desta investigação.

**Mensagens efêmeras.** Mensagens não são persistidas em banco de dados; existem apenas durante a sessão ativa e são descartadas ao seu término. Essa escolha de design proporciona a propriedade de *forward secrecy* da camada de transporte: o eventual comprometimento futuro do servidor não permitirá a leitura de mensagens passadas.

**Apenas texto.** Suporte a anexos, áudio, vídeo ou outras mídias não está no escopo. A discussão criptográfica é a mesma; o engenheiramento adicional não acrescentaria contribuição científica relevante.

**Quatro modos selecionáveis pelo usuário.** A possibilidade de o próprio usuário escolher o modo a cada sessão é a manifestação concreta do propósito comparativo do sistema: a aplicação não advoga por um modo específico; ela permite que cada usuário (e, na prática experimental, cada execução automatizada) opere em condições idênticas para qualquer um dos quatro modos.

---

## 6. O Que o Sistema Não Faz

Documentar explicitamente os limites do escopo é tão importante quanto documentar o que é entregue. O QChat:

- **Não é um aplicativo de mensageria comercial.** Não pretende substituir Signal, WhatsApp ou similares.
- **Não opera sobre hardware quântico real.** O canal quântico é simulado por meio do Qiskit Aer. Resultados em hardware fotônico real poderiam divergir dos observados.
- **Não considera todos os modelos de ataque possíveis.** Ataques de canal lateral (*side-channel*), comprometimento de *endpoint*, *malware* no cliente e ataques físicos ao hardware estão fora do escopo. O modelo de ameaças formal está documentado no Capítulo 3 do TCC.
- **Não persiste mensagens.** Histórico de conversas anteriores não é recuperável após o encerramento da sessão. Essa é uma decisão de design, não uma limitação a corrigir.
- **Não suporta grupos.** A extensão para conversas com mais de dois participantes está identificada como direção de trabalho futuro.
- **Não fornece autenticação inicial dos usuários por meios fortes.** O cadastro com usuário e senha é o mínimo necessário para que sessões possam ser estabelecidas; cenários de mundo real exigiriam autenticação mais robusta (autenticação por dois fatores, identidade federada, atestação de hardware), que estão fora do foco da investigação.

---

## 7. Critérios de Sucesso

O sucesso do QChat será avaliado por critérios objetivos derivados dos requisitos do TCC.

### 7.1 Critérios funcionais

- A aplicação está acessível por URL pública durante o período de avaliação da banca.
- Os quatro modos de estabelecimento de chave funcionam de forma completa, ponta-a-ponta.
- O pipeline BB84 implementa as etapas de *sifting*, estimativa de QBER, reconciliação por Cascade e *privacy amplification* — não apenas a geração inicial de bits.
- A detecção de espionagem é demonstrável: ativando Eve em modo *intercept-resend*, o sistema reconhece a perturbação e encerra a sessão.
- Logs estruturados são gerados em formato consumível para análise experimental.

### 7.2 Critérios de qualidade

- Cobertura de testes automatizados igual ou superior a 85% nos módulos criptográficos.
- Código-fonte disponível publicamente sob licença *open-source* permissiva.
- Documentação de implantação permitindo que terceiros subam a aplicação localmente em até cinco minutos a partir do repositório.

### 7.3 Critérios investigativos

- Os quatro experimentos previstos no Capítulo 4 do TCC podem ser executados de forma reproduzível a partir de *scripts* fornecidos.
- Resultados quantitativos sobre tempo de estabelecimento, QBER sob ataque, *throughput* e robustez do esquema híbrido são coletados e analisados.
- Os resultados permitem responder objetivamente à pergunta de pesquisa formulada no TCC.

---

## 8. Disponibilização

O QChat é disponibilizado em três formas complementares:

**Aplicação em produção** — URL pública e acessível durante o período de avaliação do TCC, permitindo que a banca, examinadores externos e a comunidade interajam com a aplicação sem necessidade de instalação local.

**Código-fonte** — repositório público em plataforma de hospedagem de código sob licença MIT, contemplando código, testes, *scripts* de experimento, documentação e *workflows* de integração contínua.

**Documentação** — incluindo o próprio TCC (em formato PDF), *README* do repositório, guia de implantação e documentação da API gerada automaticamente a partir das anotações do código.

---

## 9. Continuidade

Como artefato vinculado a um Trabalho de Conclusão de Curso, o QChat tem ciclo de vida primário associado à defesa e à avaliação acadêmica. Após esse período, as seguintes evoluções foram identificadas como direções de continuidade que podem dar origem a novos trabalhos investigativos:

- Migração da simulação quântica para hardware fotônico real, por meio de parceria com laboratório de pesquisa em óptica quântica.
- Investigação de protocolos QKD resistentes a ataques de canal lateral, em particular *Measurement-Device-Independent QKD*.
- Extensão para mensageria em grupo, integrando o esquema híbrido ao protocolo MLS (RFC 9420).
- Avaliação de outros mecanismos pós-quânticos padronizados pelo NIST, em particular o HQC selecionado em 2025.
- Integração de assinaturas pós-quânticas (ML-DSA ou SLH-DSA) à camada de autenticação, completando a transição da pilha criptográfica.
- Análise formal de segurança composta do esquema híbrido em modelo de *Universal Composability* ou modelo baseado em jogos.

Essas direções são detalhadas no Capítulo 5 do TCC.

---

## 10. Glossário

**AES-256-GCM** — *Advanced Encryption Standard* em modo *Galois/Counter Mode*; cifra simétrica autenticada padronizada pelo NIST, utilizada para cifrar as mensagens da sessão.

**BB84** — primeiro protocolo de Distribuição de Chaves Quânticas, proposto por Bennett e Brassard em 1984.

***Forward secrecy*** — propriedade segundo a qual o comprometimento futuro de chaves de longo prazo não permite decifrar mensagens passadas.

**HKDF** — *HMAC-based Key Derivation Function*; função de derivação de chave padronizada pelo IETF (RFC 5869), utilizada para combinar as chaves provenientes de BB84 e ML-KEM no modo híbrido.

**ML-KEM** — *Module-Lattice-Based Key-Encapsulation Mechanism*; algoritmo pós-quântico para encapsulamento de chave, padronizado pelo NIST em 2024 como FIPS 203.

**NIST** — *National Institute of Standards and Technology*; agência norte-americana responsável pela padronização técnica, incluindo os padrões pós-quânticos.

**PQC** — *Post-Quantum Cryptography*; classe de algoritmos criptográficos resistentes a ataques de computadores quânticos, operando sobre hardware convencional.

**QBER** — *Quantum Bit Error Rate*; taxa de discrepâncias entre as chaves de Alice e Bob após o *sifting*, métrica fundamental para detecção de espionagem em QKD.

**QKD** — *Quantum Key Distribution*; classe de protocolos para estabelecimento de chaves apoiados em princípios da mecânica quântica.

**RSA** — Rivest, Shamir e Adleman; algoritmo de criptografia de chave pública clássico, utilizado neste sistema apenas como controle experimental.

**TLS** — *Transport Layer Security*; protocolo padrão da Internet para canal autenticado e cifrado, utilizado como base do canal clássico requerido pelos protocolos de QKD.

Com base nos princípios de engenharia de software detalhados nas fontes — que vão desde o *Design by Contract* (DbC), princípios SOLID, Arquitetura Limpa (Clean Architecture) até as especificidades do Python como `Abstract Base Classes` (ABCs) e `Protocols` — elaborei um **"Contrato de Design de Software para Python"**. 

Este documento serve como um manifesto ou guia de boas práticas para garantir que o código seja limpo, flexível, testável e previsível.

---

# 📜 O Contrato de Design de Software em Python

### Cláusula 1: A Promessa da Interface e Tipagem (ABCs vs. Protocols)
Nós nos comprometemos a definir claramente como os objetos se comunicam, escolhendo a abstração correta para cada cenário:
*   **Contratos Rígidos (ABCs):** Usaremos *Abstract Base Classes* (módulo `abc`) quando precisarmos impor uma hierarquia estrita e garantir que as subclasses implementem métodos específicos sob pena de erro em tempo de execução.
*   **Contratos Flexíveis (Protocols):** Usaremos `typing.Protocol` para criar *duck typing* estático (subtipagem estrutural). Se um objeto externo tiver os métodos necessários, ele cumpre o contrato sem precisar herdar da nossa classe, favorecendo o baixo acoplamento.

### Cláusula 2: A Promessa de Estado e Ação (Properties vs. Métodos)
Nós nos comprometemos a não surpreender outros desenvolvedores com comportamentos ocultos:
*   **Uso de `@property`:** Utilizaremos propriedades apenas para acessar estados ou calcular estados derivados simples de forma rápida, determinística e segura.
*   **O que uma propriedade NÃO fará:** Nunca usaremos `@property` para operações de I/O (como salvar no banco de dados) ou tarefas assíncronas (`async`). Se a operação exige espera, consome recursos pesados ou pode falhar, **ela será um método**.

### Cláusula 3: O Contrato de Comportamento (Design by Contract - DbC)
Trataremos a relação entre funções (fornecedores) e quem as chama (clientes) como um contrato de negócios formal:
*   **Pré-condições (Obrigação do Cliente):** Definiremos claramente o estado em que o sistema deve estar antes de uma função ser chamada (ex: garantir que uma lista não esteja vazia antes de buscar seu valor máximo).
*   **Pós-condições (Garantia do Fornecedor):** Garantiremos que, se as pré-condições forem atendidas, o método entregará o resultado esperado (ex: o valor retornado será de fato o maior da lista). As pós-condições servirão como nossa principal fonte da verdade para testes.

### Cláusula 4: O Contrato de Arquitetura (Clean & Hexagonal Architecture)
Garantiremos que nossa regra de negócios seja isolada do mundo exterior (bancos de dados, frameworks, UI):
*   **A Regra de Dependência:** As dependências do código sempre apontarão de fora para dentro. Frameworks dependem de Adaptadores, Adaptadores dependem de Casos de Uso, e Casos de Uso dependem de Entidades.
*   **Portas e Adaptadores:** O "core" da nossa aplicação não saberá de onde vêm os dados. Criaremos *Portas* (interfaces) que os *Adaptadores* (bancos de dados, APIs) deverão implementar.

### Cláusula 5: O Contrato de Acoplamento (Princípios SOLID e Injeção de Dependência)
Escreveremos código que seja fácil de manter e estender, adotando os princípios SOLID:
*   **Responsabilidade Única (SRP):** Cada classe terá apenas um único motivo para mudar (uma única responsabilidade).
*   **Aberto/Fechado (OCP):** O código será aberto para extensão (podemos adicionar novos recursos), mas fechado para modificação (não alteraremos código existente que já funciona).
*   **Substituição de Liskov (LSP):** Uma subclasse sempre poderá substituir sua classe base sem quebrar o comportamento do programa (ex: um `Quadrado` não deve herdar de `Retangulo` se isso for quebrar as expectativas de largura e altura independentes).
*   **Inversão de Dependência (DIP) e Injeção:** Módulos de alto nível não dependerão de detalhes de implementação. Em vez de instanciar dependências rígidas (alto acoplamento), nós as *injetaremos* de fora (baixo acoplamento), usando interfaces ou frameworks de Injeção de Dependência para facilitar os testes e a troca de componentes.

### Cláusula 6: O Contrato dos Testes (TDD)
*   **Testes como Especificação:** Os testes não serão vistos apenas como verificações de bugs, mas como documentações executáveis do comportamento esperado do sistema (aliados ao *Design by Contract*).
*   **Ritmo de Desenvolvimento:** Escreveremos o teste para o contrato antes da implementação, projetando a API da forma como ela deverá ser consumida, e não da forma que for mais fácil de implementar.

---
*Ao assinar este contrato, o desenvolvedor garante que seu código em Python comunicará claramente suas intenções (métodos vs propriedades), dependerá de abstrações em vez de implementações fixas, e isolará as regras de negócio das ferramentas de infraestrutura.*

# bookmarks-client

## Sobre o projeto

O projeto consiste uma aplicação web que interage com uma api REST para salvar booksmarks dos usuários.

Repositório do projeto com a API (feito em Node-js) [https://github.com/diegorocha/bookmarks-api](https://github.com/diegorocha/bookmarks-api)

Esse projeto poderia ser todo feito com Javascript, utilizando Angular ou React para gerir toda inteligência da aplicação e fazer as requsições ao Nodejs.

Porém, um dos requisitos do projeto era ser feito em python, com Flask ou Django. Optei pelo desenvolvimento com Django, por ser o framework que eu possuo mais familiridade, mas o Flask também atenderia muito bem pra esse projeto.

Dessa forma, o python está sendo utilizado basicamente para fazer as requisições a API, e o django se encarrega do sistemas de templates e session.

Uma vezes que o python ficou responsável por fazer a comunicação com a API e com as regras de negócio, o javascrit ficou responsável apenas pelos efeitos visuais/animações.

Para isso optei pelo jQuery, pois o mesmo já estava adicionado ao projeto, uma vez que o bootstrap depende dele.

## Observações

O projeto foi feito focando na simplicidade, a interface de usuário é bem minimalista (bootstrap puro, sem nenhum ajuste). Algumas validações foram omitidas (por exemplo no client na api, confirmação antes de remover, etc), bem como me limitei as features especificadas no enunciado.

Ainda assim, o mesmo está preparado para "produção", as configurações importantes do django estão encapsuladas com o [python-decouple](https://github.com/henriquebastos/django-decouple).

O python-decouple me possibilita "setar" essas configurações através de variáveis de ambiente ou de um arquivo .env na raiz do projeto

Também simplicifade do desenvolvimento adotei o sqlite (valor padrão quando nenhum banco é especificado), mas, se o projeto fosse real deveria ser um basco mais escalável, como postgres.



## Instalação

Para executar o projeto localmente basta clonar o repositório.

Instalar as dependências do python com o pip (preferencialmente dentro de uma virtualenv).

```shell
pip install -r requirements.txt
python manange.py migrate
python manage.py runserver
```

## Testes

Para executar os testes unitários basta rodar o comando test do Makefile

Instalar as depências do python com o pip (preferencialmente dentro de uma virtualenv).

```shell
make test
```

Esse comando, além de chamar a suite de testes do Django, gera o relatório (em HTML) da cobertura de testes, e salva na pasta "coverage"

## Docker

Para executar o projeto dentro de um container docker:

```shell
docker build -t bookmarks-client .
docker run -p 8000:80 -d bookmarks-client
```

O projeto estará disponível através de http://localhost:8000/ ou http://container-ip/

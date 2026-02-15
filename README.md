# Índices de Inflação no Brasil

Esse projeto tem o objetivo de centralizar e disponibilizar dados em JSON dos principais índices de inflação do Brasil.

## Índices Disponibilizados

| Índice          | Última Atualização | Nome                                                     | Fonte |
| --------------- | ------------------ | -------------------------------------------------------- | ----- |
| IPCA            | 01/2026            | Índice Nacional de Preços ao Consumidor Amplo            | IBGE  |
| IPCA15          | 01/2026            | Índice Nacional de Preços ao Consumidor Amplo 15         | IBGE  |
| IPCA - 12 Meses | 01/2026            | IPCA acumulado nos últimos 12 meses                      | IBGE  |
| INPC            | 01/2026            | Índice Nacional de Preços ao Consumidor                  | IBGE  |
| IGP-M           | 01/2026            | Índice Geral de Preços - Mercado                         | FGV   |
| IGP-DI          | 01/2026            | Índice Geral de Preços – Disponibilidade Interna         | FGV   |
| IPC-BR          | 01/2026            | Índice de Preços ao Consumidor - Brasil                  | FGV   |
| IPC-M           | 01/2026            | Índice de Preços ao Consumidor - Mercado                 | FGV   |
| IPC-SP          | 01/2026            | Índice de Preços ao Consumidor do Município de São Paulo | FIPE  |

Além dos índices de inflação, também é disponibilizado as **[metas de inflação](metas-de-inflacao.json)** definida pelo [Conselho Monetario Nacional (CMN)](https://www.bcb.gov.br/acessoinformacao/cmn) do Banco Central para cada ano.

## Como consultar um índice?

Você pode consultar um índice fazendo um `request` direto para o GitHub.

### Usando cURL

```shell
curl --request GET --url https://raw.githubusercontent.com/investash/inflacao/main/ipca/valores.json
```

De um ano em específico:

```shell
curl --request GET --url https://raw.githubusercontent.com/investash/inflacao/main/ipca/anos/2005.json
```

### Python

```python
import requests
url = "https://raw.githubusercontent.com/investash/inflacao/main/ipca/valores.json"
response = requests.get(url)
print(response.json())
```

De um ano em específico:

```python
import requests
url = "https://raw.githubusercontent.com/investash/inflacao/main/ipca/anos/2005.json"
response = requests.get(url)
print(response.json())
```

### Javascript - Axios

```javascript
import axios from "axios";

const options = {
  method: "GET",
  url: "https://raw.githubusercontent.com/investash/inflacao/main/ipca/valores.json",
};

try {
  const { data } = await axios.request(options);
  console.log(data);
} catch (error) {
  console.error(error);
}
```

De um ano em específico:

```javascript
import axios from "axios";

const options = {
  method: "GET",
  url: "https://raw.githubusercontent.com/investash/inflacao/main/ipca/anos/2005.json",
};

try {
  const { data } = await axios.request(options);
  console.log(data);
} catch (error) {
  console.error(error);
}
```

### PHP - Guzzle

```php
<?php

$client = new \GuzzleHttp\Client();

$response = $client->request('GET', 'https://raw.githubusercontent.com/investash/inflacao/main/ipca/anos/2005.json');

echo $response->getBody();
```

## Licença

```text
 Copyright (c) 2024 Investash

 Permission is hereby granted, free of charge, to any person obtaining a copy
 of this software and associated documentation files (the "Software"), to deal
 in the Software without restriction, including without limitation the rights
 to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 copies of the Software, and to permit persons to whom the Software is
 furnished to do so, subject to the following conditions:

 The above copyright notice and this permission notice shall be included in
 all copies or substantial portions of the Software.

 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 THE SOFTWARE.
```

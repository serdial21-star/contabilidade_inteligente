'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');

const {
  parseCsv,
  parsePdfText,
  validate,
  spreadsheetRows,
  parseMoneyToCents,
  runN8n,
} = require('./raicms_parser.js');

const fixture = (name) => fs.readFileSync(path.join(__dirname, 'fixtures', name), 'utf8');
const csv = () => fixture('raicms_valido.csv');
const pdfText = () => fixture('raicms_pdf_texto_valido.txt');
const withoutOrigin = (model) => ({ ...model, origem: undefined });

test('CSV sintético completo produz período conferido em centavos inteiros', () => {
  const model = parseCsv(csv());
  assert.equal(model.origem, 'csv');
  assert.equal(model.ano, '2026');
  assert.equal(model.periodos[0].competencia, '01/2026');
  assert.equal(model.periodos[0].entradas[0].valor_contabil, 123456);
  assert.equal(model.periodos[0].resumos.proprio.deducoes_detalhadas.length, 2);
  const result = validate(model);
  assert.equal(result.valido, true);
  assert.equal(result.divergencias.length, 0);
  assert.equal(result.alertas.length, 1);
  assert.match(result.alertas[0].motivo, /sem igualdade normativa obrigatória/);
});

test('texto de PDF fora de ordem produz o mesmo modelo canônico do CSV', () => {
  const fromCsv = parseCsv(csv());
  const fromPdf = parsePdfText(pdfText());
  assert.deepEqual(withoutOrigin(fromPdf), withoutOrigin(fromCsv));
  assert.equal(fromPdf.origem, 'pdf_texto');
  assert.equal(validate(fromPdf).valido, true);
});

test('CSV anual aceita CFOP repetido em meses distintos e preenche números por mês', () => {
  const february = csv().replaceAll('01/2026', '02/2026');
  const model = parseCsv(`${csv()}\n${february}`);
  assert.deepEqual(model.periodos.map((period) => period.competencia), ['01/2026', '02/2026']);
  assert.equal(validate(model).valido, true);
  const row = spreadsheetRows(model).find((item) => item.CFOP === '1102');
  assert.equal(row.JANEIRO, 1234.56);
  assert.equal(row.FEVEREIRO, 1234.56);
  assert.equal(typeof row.JANEIRO, 'number');
  assert.equal(row.MARÇO, 0);
});

test('soma que não fecha bloqueia a conferência do período', () => {
  const model = parseCsv(csv().replace('1.00 do Estado;1.234,56', '1.00 do Estado;1.234,55'));
  const result = validate(model);
  assert.equal(result.valido, false);
  assert.ok(result.divergencias.some((item) =>
    item.campo === 'periodos.01/2026.subtotais.entradas.1.valor_contabil'));
});

test('CFOP inválido falha fechado', () => {
  assert.throws(() => parseCsv(csv().replace('1102;', '4102;')), /CFOP inválido/);
});

test('CFOP repetido no mesmo período falha fechado', () => {
  const duplicate = csv().replace('1.00 do Estado;', '1102;1.234,56;1.000,00;180,00;100,00;134,56\n1.00 do Estado;');
  assert.throws(() => parseCsv(duplicate), /CFOP repetido em 01\/2026/);
});

test('anos divergentes falham como no baseline anual', () => {
  const otherYear = csv().replaceAll('01/2026', '02/2027');
  assert.throws(() => parseCsv(`${csv()}\n${otherYear}`), /anos diferentes/);
});

test('PDF multiperíodo na mesma página falha fechado', () => {
  const ambiguous = `${pdfText()}\nENTRADAS 02/2026`;
  assert.throws(() => parsePdfText(ambiguous), /títulos de períodos diferentes/);
});

test('linha numérica não interpretada bloqueia sem descarte silencioso', () => {
  const model = parseCsv(`${csv()}\nPágina 1 de 2`);
  const result = validate(model);
  assert.equal(result.valido, false);
  assert.ok(model.periodos[0].nao_interpretadas.some((item) => item.conteudo === 'Página 1 de 2'));
});

test('valores com milhar e zero são exatos', () => {
  assert.equal(parseMoneyToCents('1.234,56'), 123456);
  assert.equal(parseMoneyToCents('0,00'), 0);
  assert.equal(parseMoneyToCents('-10,01'), -1001);
});

test('saldo credor e excesso de dedução seguem o E110 3.2.2', () => {
  const text = csv()
    .replace('001;Débitos por saídas;270,00', '001;Débitos por saídas;100,00')
    .replace('004;Total dos débitos;270,00', '004;Total dos débitos;100,00')
    .replace('011;Saldo devedor apurado;90,00', '011;Saldo devedor apurado;0,00')
    .replace('013;ICMS a recolher;80,00', '013;ICMS a recolher;0,00')
    .replace('014;Saldo credor a transportar;0,00', '014;Saldo credor a transportar;90,00');
  const result = validate(parseCsv(text));
  assert.equal(result.valido, true);
  assert.equal(result.divergencias.length, 0);
});

test('PDF sem texto útil orienta envio em CSV', () => {
  assert.throws(() => parsePdfText(''), /PDF sem texto útil.*CSV/);
});

test('CSV anual aceita movimento, mês zerado e resumos ST opcionais', () => {
  const model = parseCsv(fixture('raicms_anual_misto.csv'));
  assert.deepEqual(model.periodos.map((period) => period.competencia), ['01/2026', '02/2026']);
  assert.equal(model.periodos[0].resumos.st_dentro.referencia, 'E210');
  assert.equal(model.periodos[0].resumos.st_fora.referencia, 'E210');
  assert.equal(model.periodos[1].resumos.st_dentro, null);
  assert.equal(validate(model).valido, true);
});

test('PDF por página associa título no fim a dois meses', () => {
  const model = parsePdfText(JSON.parse(fixture('raicms_pdf_paginas.json')));
  assert.deepEqual(model.periodos.map((period) => period.competencia), ['01/2026', '02/2026']);
  assert.equal(model.periodos[0].resumos.st_dentro.referencia, 'E210');
  assert.equal(validate(model).valido, true);
});

test('PDF sem movimentação distribui totais iguais entre entradas e saídas', () => {
  const model = parsePdfText(JSON.parse(fixture('raicms_pdf_sem_movimentacao_multiperiodo.json')));
  assert.deepEqual(model.periodos.map((period) => period.competencia), ['01/2026', '02/2026']);
  const zeroPeriod = model.periodos[1];
  assert.deepEqual(zeroPeriod.totais.entradas, {
    valor_contabil: 0,
    base_calculo: 0,
    imposto: 0,
    isentas_nao_tributadas: 0,
    outras: 0,
  });
  assert.deepEqual(zeroPeriod.totais.saidas, zeroPeriod.totais.entradas);
  assert.deepEqual(zeroPeriod.nao_interpretadas, []);
  assert.equal(validate(model).valido, true);
});

test('texto realista do n8n aceita valores antes ou depois de rótulos grudados', () => {
  const model = parsePdfText(JSON.parse(fixture('raicms_pdf_n8n_rotulos_grudados.json')));
  assert.deepEqual(model.periodos.map((period) => period.competencia), ['01/2026', '02/2026']);
  assert.equal(model.periodos[0].entradas[0].cfop, '1102');
  assert.equal(model.periodos[0].saidas[0].cfop, '5102');
  assert.equal(model.periodos[0].resumos.proprio.valores['001'], 27000);
  assert.equal(model.periodos[0].resumos.proprio.deducoes_detalhadas.length, 2);
  assert.deepEqual(model.periodos[1].nao_interpretadas, []);
  assert.equal(validate(model).valido, true);
});

test('linhas em negrito duplicadas exatamente são reduzidas nos três resumos', () => {
  const model = parsePdfText(JSON.parse(fixture('raicms_pdf_resumos_negrito_duplicados.json')));
  const summaries = model.periodos[0].resumos;
  assert.equal(summaries.proprio.valores['008'], 1800);
  assert.equal(summaries.proprio.valores['010'], 1800);
  assert.equal(summaries.st_dentro.valores['008'], 0);
  assert.equal(summaries.st_dentro.valores['010'], 0);
  assert.equal(summaries.st_fora.valores['008'], 0);
  assert.equal(summaries.st_fora.valores['010'], 0);
  assert.equal(validate(model).valido, true);
});

test('linha repetida com valor diferente não é reduzida', () => {
  const pages = JSON.parse(fixture('raicms_pdf_resumos_negrito_duplicados.json'));
  pages[2] = pages[2].replace(
    '008 Subtotal 18,00008 Subtotal 18,00',
    '008 Subtotal 18,00008 Subtotal 18,01',
  );
  const model = parsePdfText(pages);
  assert.equal(validate(model).valido, false);
  assert.ok(model.periodos[0].nao_interpretadas.some((item) =>
    item.conteudo === '008 Subtotal 18,00008 Subtotal 18,01'));
});

test('rótulo ambíguo e quantidade monetária inesperada continuam bloqueando', () => {
  const pages = JSON.parse(fixture('raicms_pdf_n8n_rotulos_grudados.json'));
  pages[0] = pages[0].replace(
    'ENTRADAS 01/2026',
    '1,00 2,00 3,00 4,001102\n1,00 1,00 1,00 1,00 1,001102 5102\nENTRADAS 01/2026',
  );
  const model = parsePdfText(pages);
  const result = validate(model);
  assert.equal(result.valido, false);
  assert.ok(model.periodos[0].nao_interpretadas.some((item) => item.conteudo.endsWith('1102')));
  assert.ok(model.periodos[0].nao_interpretadas.some((item) => item.conteudo.endsWith('1102 5102')));
});

test('página numérica sem título e anos distintos falham fechado', () => {
  assert.throws(() => parsePdfText(['1102 1,00 1,00 0,18 0,00 0,00']), /não possui título/);
  const pages = JSON.parse(fixture('raicms_pdf_paginas.json'));
  pages.push('ENTRADAS 03/2027');
  assert.throws(() => parsePdfText(pages), /anos diferentes/);
});

test('arquivo inteiro sem CFOP responde como nada a gerar, sem divergências', () => {
  const text = fixture('raicms_sem_movimentacao.csv');
  assert.equal(validate(parseCsv(text)).valido, true);
  const result = runN8n([{ json: { origem: 'csv', texto: text } }])[0].json;
  assert.equal(result.success, false);
  assert.equal(result.gerarPlanilha, false);
  assert.equal(result.semMovimentacao, true);
  assert.match(result.message, /Sem movimentação de CFOP/);
  assert.deepEqual(result.divergencias, []);
  assert.deepEqual(result.listaAtualizacao, []);
});

test('código repetido é isolado por tipo e título ST desconhecido falha', () => {
  const model = parseCsv(fixture('raicms_anual_misto.csv'));
  assert.equal(model.periodos[0].resumos.proprio.valores['001'], 3600);
  assert.equal(model.periodos[0].resumos.st_dentro.valores['001'], 2000);
  assert.throws(() => parseCsv(csv().replace(
    'Resumo Apuração - ICMS 01/2026',
    'Resumo Apuração do ICMS - Substituição Tributária - Interestadual 01/2026',
  )), /Título de resumo ST não reconhecido/);
});

'use strict';

// Convênio SINIEF s/nº/1970, modelo 9; Guia EFD-ICMS/IPI 3.2.2:
// E110 (PDF 223–225) e E210 (PDF 229–232). Acesso em 04/10/2026.
const MONEY_PATTERN = /-?(?:\d{1,3}(?:\.\d{3})+|\d+),\d{2}/g;
const ENTRY_GROUPS = ['1', '2', '3'];
const EXIT_GROUPS = ['5', '6', '7'];
const SUMMARY_TYPES = ['proprio', 'st_dentro', 'st_fora'];
const SUMMARY_CODES = Array.from({ length: 14 }, (_, i) => String(i + 1).padStart(3, '0'));
const COLUMNS = ['valor_contabil', 'base_calculo', 'imposto', 'isentas_nao_tributadas', 'outras'];
const MONTHS = ['JANEIRO', 'FEVEREIRO', 'MARÇO', 'ABRIL', 'MAIO', 'JUNHO', 'JULHO', 'AGOSTO', 'SETEMBRO', 'OUTUBRO', 'NOVEMBRO', 'DEZEMBRO'];
const DETAILS = ['ADICIONAL RELATIVO AO FUNDO DE COMBATE A POBREZA', 'DEDUCAO RELATIVA AO INCENTIVO A CULTURA'];

function fold(value) { return String(value ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toUpperCase(); }
function cleanLine(value) { return String(value ?? '').replace(/\u00a0/g, ' ').replace(/^[;|\s]+/, '').trim(); }
function parseMoneyToCents(value) {
  const raw = String(value ?? '').trim().replace(/\s/g, '');
  if (!/^-?(?:\d{1,3}(?:\.\d{3})+|\d+),\d{2}$/.test(raw)) throw new Error(`Valor monetário inválido: ${value}`);
  const negative = raw.startsWith('-');
  const digits = (negative ? raw.slice(1) : raw).replace(/\./g, '').replace(',', '');
  let cents = 0;
  for (const digit of digits) {
    cents = cents * 10 + digit.charCodeAt(0) - 48;
    if (cents > 9007199254740991) throw new Error(`Valor monetário fora do intervalo seguro: ${raw}`);
  }
  return negative ? -cents : cents;
}
function formatCents(cents) {
  const absolute = Math.abs(cents);
  return `${cents < 0 ? '-' : ''}${Math.trunc(absolute / 100)},${String(absolute % 100).padStart(2, '0')}`;
}
function moneyValues(line) { return [...String(line).matchAll(MONEY_PATTERN)].map((m) => parseMoneyToCents(m[0])); }
function valuesObject(values) { return Object.fromEntries(COLUMNS.map((column, i) => [column, values[i]])); }
function rowVector(row) { return COLUMNS.map((column) => row[column]); }
function addVectors(vectors) {
  const result = [0, 0, 0, 0, 0];
  for (const vector of vectors) for (let i = 0; i < 5; i += 1) {
    result[i] += vector[i];
    if (Math.abs(result[i]) > 9007199254740991) throw new Error('Soma monetária fora do intervalo seguro.');
  }
  return result;
}
function vectorsEqual(a, b) { return a.length === b.length && a.every((value, i) => value === b[i]); }

function titleInfo(line) {
  const text = fold(cleanLine(line));
  if (!/^(?:ENTRADAS|SAIDAS)\b|^RESUMO.*APURACAO/.test(text)) return null;
  const match = text.match(/\b(0?[1-9]|1[0-2])\/(\d{4})\b/);
  if (!match) throw new Error(`Título sem competência reconhecível: ${cleanLine(line)}.`);
  const competencia = `${match[1].padStart(2, '0')}/${match[2]}`;
  if (/\bENTRADAS\b/.test(text)) return { competencia, secao: 'entradas', resumoTipo: null };
  if (/\bSAIDAS\b/.test(text)) return { competencia, secao: 'saidas', resumoTipo: null };
  if (/SUBSTITUICAO TRIBUTARIA/.test(text)) {
    if (/DENTRO DO ESTADO/.test(text)) return { competencia, secao: 'resumo', resumoTipo: 'st_dentro' };
    if (/FORA DO ESTADO/.test(text)) return { competencia, secao: 'resumo', resumoTipo: 'st_fora' };
    throw new Error(`Título de resumo ST não reconhecido: ${cleanLine(line)}.`);
  }
  if (/RESUMO.*APURACAO.*ICMS/.test(text)) return { competencia, secao: 'resumo', resumoTipo: 'proprio' };
  throw new Error(`Título de resumo não reconhecido: ${cleanLine(line)}.`);
}
function newSummary() { return { valores: {}, campos_normativos: {}, deducoes_detalhadas: [] }; }
function newPeriod(competencia) {
  return { competencia, entradas: [], saidas: [], subtotais: { entradas: {}, saidas: {} }, totais: { entradas: null, saidas: null }, resumos: { proprio: null, st_dentro: null, st_fora: null }, nao_interpretadas: [], _totals: [], _cfops: new Set() };
}
function populateNames(summary, type) {
  if (!summary) return;
  const names = { '001': 'VL_TOT_DEBITOS', '002': 'OUTROS_DEBITOS', '003': 'VL_ESTORNOS_CRED', '004': 'TOTAL_DEBITOS', '005': 'VL_TOT_CREDITOS', '006': 'OUTROS_CREDITOS', '007': 'VL_ESTORNOS_DEB', '008': 'TOTAL_CREDITOS', '009': 'VL_SLD_CREDOR_ANT', '010': 'TOTAL_CREDITOS_COM_SALDO_ANTERIOR', '011': 'VL_SLD_APURADO', '012': 'VL_TOT_DED', '013': 'VL_ICMS_RECOLHER', '014': 'VL_SLD_CREDOR_TRANSPORTAR' };
  for (const [code, name] of Object.entries(names)) if (summary.valores[code] !== undefined) summary.campos_normativos[name] = summary.valores[code];
  summary.referencia = type === 'proprio' ? 'E110' : 'E210';
}
function pageRecords(page, pageIndex) {
  const lines = String(page ?? '').replace(/^\uFEFF/, '').replace(/\u00a0/g, ' ').split(/\r?\n/).map((line) => line.trimEnd()).filter((line) => line.trim());
  const titles = lines.map(titleInfo).filter(Boolean);
  if (!titles.length) {
    if (lines.some((line) => /\d/.test(cleanLine(line)))) throw new Error(`Página ${pageIndex + 1} contém linhas numéricas, mas não possui título com competência.`);
    return [];
  }
  const competences = [...new Set(titles.map((title) => title.competencia))];
  if (competences.length !== 1) throw new Error(`Página ${pageIndex + 1} contém títulos de períodos diferentes.`);
  const types = [...new Set(titles.map((title) => title.resumoTipo).filter(Boolean))];
  if (types.length > 1) throw new Error(`Página ${pageIndex + 1} contém mais de um tipo de resumo.`);
  const sections = [...new Set(titles.map((title) => title.secao).filter((section) => section !== 'resumo'))];
  return lines.map((line, i) => ({ line, lineNumber: `${pageIndex + 1}.${i + 1}`, competence: competences[0], summaryType: types[0] ?? null, section: sections.length === 1 ? sections[0] : null }));
}
function sourceRecords(source, origin) {
  if (origin === 'pdf_texto') {
    const pages = Array.isArray(source) ? source : [source];
    if (!pages.some((page) => String(page ?? '').trim())) throw new Error('PDF sem texto útil; envie o relatório em CSV.');
    return pages.flatMap(pageRecords);
  }
  const lines = String(source ?? '').replace(/^\uFEFF/, '').replace(/\u00a0/g, ' ').split(/\r?\n/).map((line) => line.trimEnd()).filter((line) => line.trim());
  if (!lines.length) throw new Error('CSV vazio ou sem texto útil.');
  return lines.map((line, i) => ({ line, lineNumber: i + 1 }));
}
function classifyTotals(period) {
  const entry = ENTRY_GROUPS.every((g) => period.subtotais.entradas[g]) ? addVectors(ENTRY_GROUPS.map((g) => rowVector(period.subtotais.entradas[g]))) : null;
  const exit = EXIT_GROUPS.every((g) => period.subtotais.saidas[g]) ? addVectors(EXIT_GROUPS.map((g) => rowVector(period.subtotais.saidas[g]))) : null;
  for (const candidate of period._totals) {
    const isEntry = entry && vectorsEqual(candidate.values, entry);
    const isExit = exit && vectorsEqual(candidate.values, exit);
    if (isEntry && !period.totais.entradas) period.totais.entradas = valuesObject(candidate.values);
    else if (isExit && !period.totais.saidas) period.totais.saidas = valuesObject(candidate.values);
    else period.nao_interpretadas.push({ linha: candidate.lineNumber, conteudo: candidate.line });
  }
}

function parseText(source, origin) {
  const records = sourceRecords(source, origin);
  const titles = records.map((record) => titleInfo(record.line)).filter(Boolean);
  if (!titles.length) throw new Error('Competência mm/aaaa não encontrada nos títulos.');
  const competences = [...new Set(titles.map((title) => title.competencia))].sort();
  const years = new Set(competences.map((competence) => competence.slice(3)));
  if (years.size > 1) throw new Error(`O arquivo contém anos diferentes: ${[...years].sort().join(', ')}.`);
  const periods = new Map(competences.map((competence) => [competence, newPeriod(competence)]));
  const globalUnrecognized = [];
  let currentPeriod = null; let currentSection = null; let currentType = null;
  for (const record of records) {
    const line = cleanLine(record.line); const normalized = fold(line); const title = titleInfo(line);
    if (title) {
      if (origin === 'csv') { currentPeriod = periods.get(title.competencia); currentSection = title.secao; currentType = title.resumoTipo; }
      continue;
    }
    if (/^(CFOP|SUBTOTAIS?\b|OPERACOES COM |DEBITO DO IMPOSTO |VALORES\b|\*+$|\*+ SEM MOVIMENTACAO \*+$)/.test(normalized)) continue;
    const values = moneyValues(line);
    const period = periods.get(record.competence ?? currentPeriod?.competencia);
    const section = record.section ?? currentSection;
    const type = record.summaryType ?? currentType;
    if (!period) { if (/\d/.test(line)) globalUnrecognized.push({ linha: record.lineNumber, conteudo: line }); continue; }
    const cfopMatch = line.match(/^\s*(\d{4})(?=\D|$)/);
    if (cfopMatch && values.length === 5) {
      const cfop = cfopMatch[1];
      if (!ENTRY_GROUPS.includes(cfop[0]) && !EXIT_GROUPS.includes(cfop[0])) throw new Error(`CFOP inválido na linha ${record.lineNumber}: ${cfop}.`);
      if (period._cfops.has(cfop)) throw new Error(`CFOP repetido em ${period.competencia}: ${cfop}.`);
      period._cfops.add(cfop);
      (ENTRY_GROUPS.includes(cfop[0]) ? period.entradas : period.saidas).push({ cfop, ...valuesObject(values) }); continue;
    }
    const subtotal = normalized.match(/^([123567])\.00\b/);
    if (subtotal && values.length === 5) {
      const group = subtotal[1]; const side = ENTRY_GROUPS.includes(group) ? 'entradas' : 'saidas';
      if (period.subtotais[side][group]) throw new Error(`Subtotal ${group}.00 repetido em ${period.competencia}.`);
      period.subtotais[side][group] = valuesObject(values); continue;
    }
    if (/\bTOTAL\b/.test(normalized) && values.length === 5) {
      let side = /ENTRADAS/.test(normalized) ? 'entradas' : (/SAIDAS/.test(normalized) ? 'saidas' : null);
      if (!side && ['entradas', 'saidas'].includes(section)) side = section;
      if (side && !period.totais[side]) period.totais[side] = valuesObject(values);
      else period._totals.push({ values, line, lineNumber: record.lineNumber });
      continue;
    }
    if (DETAILS.some((label) => normalized.startsWith(label)) && values.length === 1) {
      if (!type) throw new Error(`Detalhamento 012 sem título de resumo na linha ${record.lineNumber}.`);
      if (!period.resumos[type]) period.resumos[type] = newSummary();
      const monetary = line.match(MONEY_PATTERN)?.[0] ?? '';
      period.resumos[type].deducoes_detalhadas.push({ descricao: (monetary ? line.slice(0, line.lastIndexOf(monetary)) : line).replace(/[;|\s]+$/, ''), valor: values[0] }); continue;
    }
    const summaryCode = normalized.match(/^\s*(00[1-9]|01[0-4])(?:\D|$)/);
    if (summaryCode && values.length) {
      if (!type) throw new Error(`Código de resumo sem título reconhecido na linha ${record.lineNumber}.`);
      if (!period.resumos[type]) period.resumos[type] = newSummary();
      const code = summaryCode[1];
      if (period.resumos[type].valores[code] !== undefined) throw new Error(`Código de resumo repetido em ${period.competencia}/${type}: ${code}.`);
      period.resumos[type].valores[code] = values.at(-1); continue;
    }
    if (/\d/.test(line)) period.nao_interpretadas.push({ linha: record.lineNumber, conteudo: line });
  }
  for (const period of periods.values()) {
    classifyTotals(period); SUMMARY_TYPES.forEach((type) => populateNames(period.resumos[type], type)); delete period._totals; delete period._cfops;
  }
  return { ano: [...years][0], origem: origin, periodos: [...periods.values()].sort((a, b) => a.competencia.localeCompare(b.competencia)), nao_interpretadas: globalUnrecognized };
}
function parseCsv(text) { return parseText(text, 'csv'); }
function parsePdfText(textOrPages) { return parseText(textOrPages, 'pdf_texto'); }
function difference(list, field, expected, found) { list.push({ campo: field, esperado: typeof expected === 'number' ? formatCents(expected) : String(expected), encontrado: typeof found === 'number' ? formatCents(found) : String(found) }); }

function validateSummary(period, type, summary, divergencias, alertas) {
  const prefix = `periodos.${period.competencia}.resumos.${type}`; const r = summary.valores;
  for (const code of SUMMARY_CODES) if (r[code] === undefined) difference(divergencias, `${prefix}.${code}`, 'presente', 'ausente');
  const check = (code, expected) => { if (r[code] !== undefined && r[code] !== expected) difference(divergencias, `${prefix}.${code}`, expected, r[code]); };
  if (['001', '002', '003'].every((code) => r[code] !== undefined)) check('004', r['001'] + r['002'] + r['003']);
  if (['005', '006', '007'].every((code) => r[code] !== undefined)) check('008', r['005'] + r['006'] + r['007']);
  if (['008', '009'].every((code) => r[code] !== undefined)) check('010', r['008'] + r['009']);
  if (r['004'] !== undefined && r['010'] !== undefined) {
    check('011', Math.max(r['004'] - r['010'], 0));
    if (r['012'] !== undefined) { check('013', Math.max(Math.max(r['004'] - r['010'], 0) - r['012'], 0)); check('014', Math.max(r['010'] + r['012'] - r['004'], 0)); }
  }
  if (summary.deducoes_detalhadas.length && r['012'] !== undefined) {
    const detailed = summary.deducoes_detalhadas.reduce((sum, item) => sum + item.valor, 0);
    if (detailed !== r['012']) alertas.push({ campo: `${prefix}.deducoes_detalhadas`, esperado: formatCents(r['012']), encontrado: formatCents(detailed), motivo: 'Detalhamento informativo sem igualdade normativa obrigatória identificada.' });
  }
  if (type === 'proprio' && period.totais.saidas && r['001'] !== undefined && period.totais.saidas.imposto !== r['001']) alertas.push({ campo: `${prefix}.001_x_total_saidas.imposto`, esperado: formatCents(period.totais.saidas.imposto), encontrado: formatCents(r['001']), motivo: 'O E110 prevê inclusões e exclusões que o relatório agregado não permite reconstruir.' });
  if (type === 'proprio' && period.totais.entradas && r['005'] !== undefined && period.totais.entradas.imposto !== r['005']) alertas.push({ campo: `${prefix}.005_x_total_entradas.imposto`, esperado: formatCents(period.totais.entradas.imposto), encontrado: formatCents(r['005']), motivo: 'O E110 prevê inclusões e exclusões que o relatório agregado não permite reconstruir.' });
}
function validatePeriod(period, divergencias, alertas) {
  const prefix = `periodos.${period.competencia}`;
  for (const [side, groups] of [['entradas', ENTRY_GROUPS], ['saidas', EXIT_GROUPS]]) {
    for (const group of groups) {
      const subtotal = period.subtotais[side][group];
      if (!subtotal) { difference(divergencias, `${prefix}.subtotais.${side}.${group}`, 'presente', 'ausente'); continue; }
      const expected = addVectors(period[side].filter((row) => row.cfop[0] === group).map(rowVector));
      COLUMNS.forEach((column, i) => { if (subtotal[column] !== expected[i]) difference(divergencias, `${prefix}.subtotais.${side}.${group}.${column}`, expected[i], subtotal[column]); });
    }
    const total = period.totais[side];
    if (!total) difference(divergencias, `${prefix}.totais.${side}`, 'presente', 'ausente');
    else if (groups.every((group) => period.subtotais[side][group])) {
      const expected = addVectors(groups.map((group) => rowVector(period.subtotais[side][group])));
      COLUMNS.forEach((column, i) => { if (total[column] !== expected[i]) difference(divergencias, `${prefix}.totais.${side}.${column}`, expected[i], total[column]); });
    }
  }
  SUMMARY_TYPES.forEach((type) => { if (period.resumos[type]) validateSummary(period, type, period.resumos[type], divergencias, alertas); });
  period.nao_interpretadas.forEach((item) => difference(divergencias, `${prefix}.linha.${item.linha}`, 'linha numérica reconhecida', item.conteudo));
}
function validate(model) {
  const divergencias = []; const alertas = [];
  model.periodos.forEach((period) => validatePeriod(period, divergencias, alertas));
  model.nao_interpretadas.forEach((item) => difference(divergencias, `linha.${item.linha}`, 'linha numérica associada a um período', item.conteudo));
  return { valido: divergencias.length === 0, divergencias, alertas };
}
function spreadsheetRows(model) {
  const rows = new Map();
  for (const period of model.periodos) for (const source of [...period.entradas, ...period.saidas]) {
    if (!rows.has(source.cfop)) rows.set(source.cfop, Array(12).fill(0));
    const month = parseInt(period.competencia.slice(0, 2), 10) - 1; rows.get(source.cfop)[month] += source.valor_contabil;
    if (Math.abs(rows.get(source.cfop)[month]) > 9007199254740991) throw new Error('Soma monetária fora do intervalo seguro na saída da planilha.');
  }
  return [...rows.entries()].sort(([a], [b]) => a.localeCompare(b)).map(([cfop, cents]) => {
    const output = { CFOP: cfop }; MONTHS.forEach((month, i) => { output[month] = cents[i] / 100; }); return output;
  });
}
function runN8n(items) {
  try {
    const input = items[0]?.json ?? {}; const model = input.origem === 'pdf_texto' ? parsePdfText(input.texto) : parseCsv(input.texto); const checked = validate(model);
    const hasCfops = model.periodos.some((period) => period.entradas.length || period.saidas.length); const noMovement = checked.valido && !hasCfops;
    return [{ json: { success: checked.valido, gerarPlanilha: checked.valido && hasCfops, semMovimentacao: noMovement, message: noMovement ? 'Sem movimentação de CFOP no período informado.' : (checked.valido ? 'Arquivo conferido.' : 'O arquivo não pôde ser conferido.'), modelo: model, divergencias: checked.divergencias, alertas: checked.alertas, listaAtualizacao: checked.valido && hasCfops ? spreadsheetRows(model) : [], totalCFOPs: checked.valido && hasCfops ? new Set(model.periodos.flatMap((period) => [...period.entradas, ...period.saidas].map((row) => row.cfop))).size : 0 } }];
  } catch (error) {
    return [{ json: { success: false, gerarPlanilha: false, semMovimentacao: false, message: 'O arquivo não pôde ser conferido.', divergencias: [{ campo: 'arquivo', esperado: 'CSV válido ou PDF com texto útil', encontrado: error.message }], alertas: [], listaAtualizacao: [], totalCFOPs: 0 } }];
  }
}
if (typeof module !== 'undefined' && module.exports) module.exports = { parseCsv, parsePdfText, validate, spreadsheetRows, parseMoneyToCents, formatCents, runN8n };
if (typeof $input !== 'undefined') return runN8n($input.all());

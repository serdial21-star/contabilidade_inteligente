(function defineIntelligenceService(root) {
  'use strict';

  const FISCAL_STATUS = Object.freeze({REPORTED_AUTHORIZED: 'Autorizada informada no XML', UNVERIFIED: 'Sem protocolo verificado', PROTOCOL_110: 'Uso denegado informado', QUARANTINED: 'Em quarentena'});

  function createIntelligenceService({dataMode, apiClient, syntheticProvider}) {
    const provider = dataMode === 'synthetic' ? syntheticProvider : Object.freeze({
      fiscalDocuments: (companyId, filters) => apiClient.fiscalDocuments(companyId, filters),
      fiscalDocument: (companyId, id) => apiClient.fiscalDocument(companyId, id),
      importNfe: (companyId, file, fields) => apiClient.importNfe(companyId, file, fields),
      bankStatements: (companyId, filters) => apiClient.bankStatements(companyId, filters),
      bankStatement: (companyId, id, filters) => apiClient.bankStatement(companyId, id, filters),
      importOfx: (companyId, file) => apiClient.importOfx(companyId, file),
      decisionLine: (companyId, rootType, id) => apiClient.decisionLine(companyId, rootType, id),
    });
    return Object.freeze({
      fiscalStatusLabel: (status) => FISCAL_STATUS[status] || 'Estado fiscal disponível no detalhe',
      fiscalDocuments: provider.fiscalDocuments,
      fiscalDocument: provider.fiscalDocument,
      importNfe: provider.importNfe,
      bankStatements: provider.bankStatements,
      bankStatement: provider.bankStatement,
      importOfx: provider.importOfx,
      decisionLine: provider.decisionLine,
    });
  }

  root.S21Intelligence = Object.freeze({createIntelligenceService, FISCAL_STATUS});
}(globalThis));

(function defineOperationalService(root) {
  'use strict';

  const STATUS_LABELS = Object.freeze({
    RECEIVED: 'Recebido', ACCEPTED: 'Recebido', DUPLICATE: 'Duplicado',
    STARTED: 'Processando', COMPLETED: 'Processado', FAILED: 'Exceção',
    QUARANTINED: 'Em quarentena',
  });

  function createOperationalService({dataMode, apiClient, syntheticProvider}) {
    const provider = dataMode === 'synthetic' ? syntheticProvider : Object.freeze({
      company: (id) => apiClient.company(id),
      documents: (id, filters) => apiClient.documents(id, filters),
      document: (companyId, documentId) => apiClient.document(companyId, documentId),
      summary: (id) => apiClient.documentSummary(id),
      updateDocumentMetadata: (companyId, documentId, payload) => apiClient.updateDocumentMetadata(companyId, documentId, payload),
      bankAccounts: (id) => apiClient.bankAccounts(id),
      createBankAccount: (id, payload) => apiClient.createBankAccount(id, payload),
      updateBankAccount: (companyId, accountId, payload) => apiClient.updateBankAccount(companyId, accountId, payload),
      setBankAccountStatus: (companyId, accountId, status) => apiClient.updateBankAccountStatus(companyId, accountId, status),
      decisionLine: (companyId, rootType, id) => apiClient.decisionLine(companyId, rootType, id),
    });
    return Object.freeze({
      statusLabel: (status) => STATUS_LABELS[status] || 'Estado indisponível',
      listCompanies(profile, search = '') {
        const term = search.trim().toLocaleLowerCase('pt-BR');
        return profile.companies.filter((company) => !term || company.name.toLocaleLowerCase('pt-BR').includes(term));
      },
      company: provider.company,
      documents: provider.documents,
      document: provider.document,
      summary: provider.summary,
      updateDocumentMetadata: provider.updateDocumentMetadata,
      bankAccounts: provider.bankAccounts,
      createBankAccount: provider.createBankAccount,
      updateBankAccount: provider.updateBankAccount,
      setBankAccountStatus: provider.setBankAccountStatus,
      decisionLine: provider.decisionLine,
    });
  }

  root.S21Operational = Object.freeze({createOperationalService, STATUS_LABELS});
}(globalThis));

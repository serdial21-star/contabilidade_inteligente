(function defineAccountingService(root) {
  'use strict';

  const STATUS = Object.freeze({
    PENDING_APPROVAL: 'Aguardando decisão profissional',
    APPROVED: 'Aprovada internamente',
    REJECTED: 'Rejeitada pelo profissional',
    BLOCKED_FOR_HOMOLOGATION: 'Aprovada, exportação bloqueada',
    SUPERSEDED: 'Substituída por nova revisão',
  });

  function createAccountingService({dataMode, apiClient, syntheticProvider}) {
    const provider = dataMode === 'synthetic' ? syntheticProvider : Object.freeze({
      accountingProposals: (companyId, filters) => apiClient.accountingProposals(companyId, filters),
      accountingProposal: (companyId, id) => apiClient.accountingProposal(companyId, id),
      proposalActivity: (companyId, id) => apiClient.proposalActivity(companyId, id),
      accountingCatalog: (companyId, effectiveAt) => apiClient.accountingCatalog(companyId, effectiveAt),
      accountingRule: (companyId, id, effectiveAt) => apiClient.accountingRule(companyId, id, effectiveAt),
      decideProposal: (companyId, id, decision, summary) => apiClient.decideProposal(companyId, id, decision, summary),
    });
    return Object.freeze({
      statusLabel: (status) => STATUS[status] || 'Estado contábil controlado',
      accountingProposals: provider.accountingProposals,
      accountingProposal: provider.accountingProposal,
      proposalActivity: provider.proposalActivity,
      accountingCatalog: provider.accountingCatalog,
      accountingRule: provider.accountingRule,
      decideProposal: provider.decideProposal,
    });
  }

  root.S21Accounting = Object.freeze({createAccountingService, STATUS});
}(globalThis));

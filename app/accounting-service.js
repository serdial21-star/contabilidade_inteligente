(function defineAccountingService(root) {
  'use strict';

  const STATUS = Object.freeze({
    PENDING_APPROVAL: 'Aguardando decisão profissional',
    APPROVED: 'Aprovada internamente',
    REJECTED: 'Rejeitada pelo profissional',
    BLOCKED_FOR_HOMOLOGATION: 'Aprovada, exportação bloqueada',
    SUPERSEDED: 'Substituída por nova revisão',
    PENDING_RULE: 'Sem regra publicada aplicável a este item',
    ACCOUNT_MAPPING_REQUIRED: 'Sem conta mapeada para a intenção classificada',
  });

  const ITEM_CLASSIFICATION_STATUS = Object.freeze({
    AUTO_CLASSIFIED: 'Classificado automaticamente pela regra vigente',
    PRE_CLASSIFIED: 'Pré-classificado, confirmação recomendada',
    REVIEW_REQUIRED: 'Aguardando classificação profissional',
    CONFLICTING_EVIDENCE: 'Evidências conflitantes, decisão profissional necessária',
    REVIEWED: 'Classificação confirmada pelo profissional',
  });

  const ACCOUNTING_INTENTS = Object.freeze({
    PURCHASE_RESALE: 'Compra para revenda',
    PURCHASE_RAW_MATERIAL: 'Compra de matéria-prima',
    PURCHASE_PACKAGING: 'Compra de embalagem',
    PURCHASE_USE_CONSUMPTION: 'Compra de uso e consumo',
    PURCHASE_FIXED_ASSET: 'Compra de imobilizado',
    PURCHASE_SERVICE: 'Compra de serviço',
    PURCHASE_MAINTENANCE: 'Compra de manutenção',
    PURCHASE_FREIGHT: 'Compra de frete',
    PURCHASE_ADMIN_EXPENSE: 'Despesa administrativa',
    PURCHASE_PROJECT_COST: 'Custo de projeto',
    PURCHASE_PREPAID_EXPENSE: 'Despesa antecipada',
    PURCHASE_OTHER: 'Outra intenção de compra',
  });

  const APPLY_SCOPE = Object.freeze({
    THIS_OCCURRENCE_ONLY: 'Somente esta ocorrência',
    SAME_ITEM_FUTURE: 'Reaproveitar para o mesmo item no futuro',
    CREATE_RULE_REQUEST: 'Solicitar criação de regra',
  });

  function createAccountingService({dataMode, apiClient, syntheticProvider}) {
    const provider = dataMode === 'synthetic' ? syntheticProvider : Object.freeze({
      accountingProposals: (companyId, filters) => apiClient.accountingProposals(companyId, filters),
      accountingProposal: (companyId, id) => apiClient.accountingProposal(companyId, id),
      proposalActivity: (companyId, id) => apiClient.proposalActivity(companyId, id),
      accountingCatalog: (companyId, effectiveAt) => apiClient.accountingCatalog(companyId, effectiveAt),
      accountingRule: (companyId, id, effectiveAt) => apiClient.accountingRule(companyId, id, effectiveAt),
      decideProposal: (companyId, id, decision, summary) => apiClient.decideProposal(companyId, id, decision, summary),
      decisionLine: (companyId, rootType, id) => apiClient.decisionLine(companyId, rootType, id),
      itemClassifications: (companyId, filters) => apiClient.itemClassifications(companyId, filters),
      itemClassification: (companyId, id) => apiClient.itemClassification(companyId, id),
      decideItemClassification: (companyId, id, decision) => apiClient.decideItemClassification(companyId, id, decision),
    });
    return Object.freeze({
      statusLabel: (status) => STATUS[status] || ITEM_CLASSIFICATION_STATUS[status] || 'Estado contábil controlado',
      itemClassificationStatusLabel: (status) => ITEM_CLASSIFICATION_STATUS[status] || 'Estado de classificação controlado',
      accountingProposals: provider.accountingProposals,
      accountingProposal: provider.accountingProposal,
      proposalActivity: provider.proposalActivity,
      accountingCatalog: provider.accountingCatalog,
      accountingRule: provider.accountingRule,
      decideProposal: provider.decideProposal,
      decisionLine: provider.decisionLine,
      itemClassifications: provider.itemClassifications,
      itemClassification: provider.itemClassification,
      decideItemClassification: provider.decideItemClassification,
    });
  }

  root.S21Accounting = Object.freeze({createAccountingService, STATUS, ACCOUNTING_INTENTS, APPLY_SCOPE});
}(globalThis));

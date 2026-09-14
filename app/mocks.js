'use strict';
// All values are synthetic presentation fixtures, not accounting configuration.
window.S21Mock = Object.freeze({
  office:'Escritório Demonstração', user:'Ana Exemplo', email:'usuario@example.invalid', date:'14/09/2026',
  companies:['Empresa Alfa Ltda.','Empresa Beta Ltda.'], owners:['Ana Exemplo','Bruno Exemplo'],
  records:[
    {id:'DOC-001',type:'NF-e',company:'Empresa Alfa Ltda.',name:'Documento sintético 001',status:'PENDING_APPROVAL',owner:'Ana Exemplo',reason:'Conferir a proposta preparada',priority:'Normal',date:'2026-09-14',time:'09:10',proposal:'PROP-001'},
    {id:'DOC-002',type:'NF-e',company:'Empresa Beta Ltda.',name:'Documento sintético 002',status:'PENDING_RULE',owner:'Bruno Exemplo',reason:'Nenhuma regra publicada aplicável',priority:'Alta',date:'2026-09-14',time:'09:15',proposal:null},
    {id:'DOC-003',type:'NF-e',company:'Empresa Alfa Ltda.',name:'Documento sintético 003',status:'BLOCKED',owner:'Ana Exemplo',reason:'Período bloqueado',priority:'Alta',date:'2026-09-14',time:'09:20',proposal:'PROP-003'},
    {id:'DOC-004',type:'NF-e',company:'Empresa Beta Ltda.',name:'Documento sintético 004',status:'APPROVED',owner:'Bruno Exemplo',reason:'Decisão humana registrada no cenário',priority:'Normal',date:'2026-09-13',time:'09:10',proposal:'PROP-004'},
    {id:'DOC-005',type:'OFX',company:'Empresa Alfa Ltda.',name:'Extrato sintético 005',status:'IMPORTED',owner:'Bruno Exemplo',reason:'Importação bancária demonstrativa',priority:'Normal',date:'2026-09-13',time:'11:00',proposal:null},
    {id:'DOC-006',type:'NF-e',company:'Empresa Beta Ltda.',name:'Documento sintético 006',status:'REJECTED',owner:'Ana Exemplo',reason:'Rejeição humana demonstrativa',priority:'Normal',date:'2026-09-12',time:'10:40',proposal:'PROP-006'}
  ],
  widgets:[
    {id:'received',label:'Documentos recebidos',value:'6',note:'Conjunto sintético completo',type:'METRIC'},
    {id:'processed',label:'Processados automaticamente',value:'5',note:'Preparação não é aprovação',type:'PROGRESS'},
    {id:'review',label:'Pendentes de revisão',value:'1',note:'Uma conferência espera por você',type:'METRIC',tone:'warning'},
    {id:'exceptions',label:'Exceções',value:'2',note:'Regra ausente e período bloqueado',type:'STATUS',tone:'warning'},
    {id:'proposals',label:'Propostas contábeis',value:'4',note:'Sem escrituração oficial',type:'METRIC'},
    {id:'approvals',label:'Aprovações pendentes',value:'2',note:'Inclui uma proposta bloqueada',type:'STATUS'},
    {id:'clients',label:'Clientes com pendências',value:'2',note:'Cenário ilustrativo',type:'LIST',items:['Empresa Alfa · revisão','Empresa Beta · regra ausente']},
    {id:'obligations',label:'Obrigações próximas',value:'2',note:'Agenda fictícia; sem obrigação fiscal real',type:'TABLE_PREVIEW',items:['Checklist sintético · 16/09','Conferência sintética · 18/09']},
    {id:'reconciliations',label:'Conciliações pendentes',value:'1',note:'Cenário conceitual; módulo operacional futuro',type:'LIST',items:['Extrato de demonstração · conferir']},
    {id:'activity',label:'Atividade recente',value:'',note:'Eventos fictícios',type:'TIMELINE',items:['09:10 · Documento recebido','09:12 · Proposta preparada','10:05 · Decisão humana (cenário aprovado)']}
  ],
  presets:{'Minha Visão':['received','processed','review','exceptions','proposals','approvals'],'Visão Executiva':['received','clients','exceptions','activity'],'Visão Contábil':['proposals','review','approvals','activity'],'Visão Fiscal':['received','processed','exceptions'],'Visão Operacional':['received','clients','obligations','reconciliations']},
  rule:'Regra ilustrativa R-01 · versão 1', debit:'Conta de débito sintética A', credit:'Conta de crédito sintética B', amount:'R$ 100,00',
  lock:{reason:'Conferência de encerramento — cenário fictício',scope:'Empresa Alfa · setembro/2026',actor:'Bruno Exemplo',date:'14/09/2026, 09:00'},
  trail:[['SOURCE','09:10','Documento recebido','Evidência sintética identificada'],['PROCESSING','09:11','XML validado','Parser demonstrativo'],['RULE','09:11','Regra aplicada','R-01 · versão 1 · cenário fictício'],['PROPOSAL','09:12','Proposta criada','Revisão ilustrativa v1 — sem efeito contábil']]
});

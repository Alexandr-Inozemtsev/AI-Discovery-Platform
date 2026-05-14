import ProjectOverviewCard from './ProjectOverviewCard'
import KnowledgeSourcesCard from './KnowledgeSourcesCard'
import ExtractedKnowledgeCard from './ExtractedKnowledgeCard'
import KnowledgeCoverageCard from './KnowledgeCoverageCard'
import AIAssistantCard from './AIAssistantCard'

export default function ContextStage(props:any){
  const allMetadataOnly=(props.sourceTrace||[]).length>0 && (props.sourceTrace||[]).every((s:any)=>s.content_level==='metadata_only')
  const fields=[
    {key:'short_description',label:'Краткое описание',value:props.contextInput.short_description,placeholder:'Кратко опишите инициативу: какой продукт, процесс или клиентский сценарий меняется',helper:'Например: Автоматизация автопролонгации ИБС для сокращения ручных операций сотрудников.'},
    {key:'product_goal',label:'Цель продукта / ожидаемый результат',value:props.contextInput.product_goal || props.contextInput.initiative_goal,placeholder:'Опишите измеримый результат, которого должен достичь продукт или процесс',helper:'Например: Сократить ручные операции на 80%, снизить ошибки и повысить клиентский опыт.'},
    {key:'business_domain',label:'Бизнес-направление',value:props.contextInput.business_domain,placeholder:'Укажите бизнес-домен или продуктовую область',helper:'Например: Банковские продукты / Индивидуальные банковские сейфы.'},
    {key:'business_process_owner',label:'Бизнес-владелец процесса',value:props.contextInput.business_process_owner || props.contextInput.process_owner,placeholder:'Укажите подразделение или роль от бизнеса, отвечающую за процесс',helper:'Например: Дирекция розничного бизнеса / владелец процесса ИБС.'},
    {key:'discovery_responsible',label:'Ответственный за Discovery',value:props.contextInput.discovery_responsible || props.contextInput.discovery_owner,placeholder:'Укажите, кто ведёт discovery и подготовку БТ',helper:'Например: Product Owner, бизнес-аналитик или ответственный сотрудник.'}
  ]
  return <div className='context-page'><div className='ui-card page-section-gap'><b>{props.contextStatus}</b></div><div className='context-layout'>
    <ProjectOverviewCard fields={fields} onChange={props.onUpdateContextField}/>
    <KnowledgeSourcesCard {...props} onRetryIndex={props.runContextAnalyze}/>
    <ExtractedKnowledgeCard knowledge={props.knowledge} sourceTrace={props.sourceTrace||[]} />
    <KnowledgeCoverageCard coverage={props.coverage || props.knowledge?.coverage || props.knowledge?.покрытие || {}} readiness={props.readiness} sourceTrace={props.sourceTrace||[]} />
    <AIAssistantCard onGoProblem={props.onGoProblem} onRefresh={props.runContextAnalyze} allMetadataOnly={allMetadataOnly} readiness={props.readiness} missingInformation={props.missingInformation||[]} problemHandoff={props.problemHandoff||props.knowledge?.problem_handoff||{}} />
  </div></div>
}

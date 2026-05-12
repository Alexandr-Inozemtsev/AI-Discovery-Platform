import ProjectOverviewCard from './ProjectOverviewCard'
import KnowledgeSourcesCard from './KnowledgeSourcesCard'
import ExtractedKnowledgeCard from './ExtractedKnowledgeCard'
import KnowledgeCoverageCard from './KnowledgeCoverageCard'
import AIAssistantCard from './AIAssistantCard'

export default function ContextStage(props:any){
  const fields=[
    ['Название инициативы',props.contextInput.initiative_name],['Краткое описание',props.contextInput.short_description],['Цель инициативы',props.contextInput.initiative_goal],['Бизнес-направление',props.contextInput.business_domain],['Владелец процесса',props.contextInput.process_owner],['Владелец Discovery',props.contextInput.discovery_owner]
  ].map(([label,value])=>({label,value:value as string}))
  return <div className='context-page'><div className='context-layout'>
    <ProjectOverviewCard fields={fields}/>
    <KnowledgeSourcesCard {...props}/>
    <ExtractedKnowledgeCard knowledge={props.knowledge} onRefresh={props.runContextAnalyze}/>
    <KnowledgeCoverageCard />
    <AIAssistantCard />
  </div></div>
}

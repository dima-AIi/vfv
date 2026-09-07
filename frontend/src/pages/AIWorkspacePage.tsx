import AIConsole from '../features/ai/AIConsole'

export default function AIWorkspacePage() {
  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">AI-ассистент</h1>
          <p className="page-subtitle">
            Центральное место работы с AI-ассистентом: выберите проект, контекст и тип действия —
            анализ, план, выполнение или сводка. Результаты сохраняются вместе с историей действий.
          </p>
        </div>
      </div>
      <AIConsole />
    </>
  )
}

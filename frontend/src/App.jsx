import SearchPage from './features/search/SearchPage'

export default function App() {
  return (
    <div className="app">
      <header className="app__header">
        <h1>MoodBite</h1>
        <p className="muted">
          Gợi ý quán ăn theo nhu cầu, vị trí và thời điểm của bạn.
        </p>
      </header>

      <main>
        <SearchPage />
      </main>

      <footer className="app__footer muted">
        Khoảng cách tính theo đường chim bay. Món ăn là suy luận từ loại hình quán,
        chưa phải thực đơn thật.
      </footer>
    </div>
  )
}

# NexBridge Frontend

React + TypeScript demo UI for NexBridge governed AI transformation.

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first styling
- **Vite** - Build tool and dev server
- **Axios** - API client (Phase 3)

## Getting Started

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build
```

The app will be available at `http://localhost:3000`

## Project Structure

```
frontend/
├── src/
│   ├── components/       # React components (Phase 2)
│   ├── types/           # TypeScript type definitions
│   ├── constants/       # Tier colours and constants
│   ├── mocks/          # Mock data for Phase 1
│   ├── services/       # API service layer
│   ├── App.tsx         # Main app component
│   ├── main.tsx        # Entry point
│   └── index.css       # Tailwind imports
├── index.html
├── vite.config.ts
├── tailwind.config.js
└── package.json
```

## Phase 1 Status

✅ Foundation scaffolded
✅ TypeScript types defined
✅ Tier colour constants
✅ Mock data created
✅ API service with mock responses
✅ Basic three-column layout

## Next Steps (Phase 2)

- Build InputPanel components
- Build PipelinePanel components
- Build OutputPanel components
- Implement agent status visualization
- Add confidence bars and tier badges

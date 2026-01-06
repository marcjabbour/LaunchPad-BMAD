#!/bin/bash

echo "Creating GitHub labels..."

gh label create "backend" --description "Backend development tasks" --color "0052cc"
gh label create "frontend" --description "Frontend/UI development tasks" --color "1d76db"
gh label create "voice" --description "Voice processing and LiveKit integration" --color "5319e7"
gh label create "ai" --description "AI/LLM integration and intelligence" --color "0e8a16"
gh label create "google-meet" --description "Google Meet integration" --color "fbca04"
gh label create "setup" --description "Environment and project setup" --color "d73a4a"
gh label create "design-system" --description "Design system and component library" --color "e99695"
gh label create "dashboard" --description "Main dashboard interface" --color "f9d0c4"
gh label create "components" --description "UI components and widgets" --color "fef2c0"
gh label create "agents" --description "Agent management and configuration" --color "c2e0c6"
gh label create "integration" --description "Frontend/backend integration" --color "bfd4f2"
gh label create "api" --description "API design and implementation" --color "bfdadc"
gh label create "architecture" --description "System architecture and planning" --color "d4c5f9"
gh label create "realtime" --description "Real-time features and WebSocket" --color "c5def5"
gh label create "intelligence" --description "Agent intelligence and behavior" --color "0e8a16"
gh label create "status" --description "Status monitoring and reporting" --color "fad8c7"

echo "✅ Labels created! Creating issues..."

gh issue create \
  --title "🔧 LiveKit Environment Setup" \
  --body "Set up LiveKit development environment and validate basic agent framework functionality. Estimate: 4 hours" \
  --label "backend,voice,setup"

gh issue create \
  --title "🗣️ Basic Google Meet Integration" \
  --body "Implement core agent that can join Google Meet calls and handle basic audio processing. Estimate: 8 hours" \
  --label "backend,voice,google-meet"

gh issue create \
  --title "🤖 OpenAI Agent Intelligence" \
  --body "Integrate OpenAI API for intelligent agent responses with basic personality and conversation memory. Estimate: 6 hours" \
  --label "backend,ai,intelligence"

gh issue create \
  --title "🎨 Next.js Foundation & Design System" \
  --body "Set up Next.js project foundation with comprehensive design system and component library. Estimate: 4 hours" \
  --label "frontend,setup,design-system"

gh issue create \
  --title "📱 Dashboard Interface" \
  --body "Create main dashboard interface that serves as the user's daily homepage for agent management. Estimate: 8 hours" \
  --label "frontend,dashboard,components"

gh issue create \
  --title "🎛️ Agent Management Interface" \
  --body "Build interface for creating, configuring, and managing AI agents. Estimate: 6 hours" \
  --label "frontend,components,agents"

gh issue create \
  --title "🔗 API Architecture Design" \
  --body "Design API contracts and real-time communication strategy between frontend and backend. Estimate: 3 hours" \
  --label "integration,api,architecture"

gh issue create \
  --title "⚡ Real-time Agent Status Integration" \
  --body "Connect backend agent status to frontend dashboard with live updates. Estimate: 4 hours" \
  --label "integration,realtime,status"

echo "🚀 All GitHub setup complete!"

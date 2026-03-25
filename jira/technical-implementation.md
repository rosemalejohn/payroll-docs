Laravel Inertia React
Objective
Build a general-purpose web application using Laravel 12 as the backend and Inertia.js with React as the frontend. The implementation should keep Laravel responsible for routing, validation, authorization, and data access, while React handles page composition and interactive UI. This blueprint is generalized and not tied to any single product domain.
Architecture Summary
Laravel is the application backbone.
Inertia is the transport layer between Laravel routes/controllers and React pages.
React is used for page-level UI and interactive components.
Vite handles frontend bundling.
Authentication, authorization, validation, queues, notifications, and database concerns remain Laravel-first.
Complex frontend state is localized; server state should come from Laravel responses or a deliberate client data layer.
Target Stack
PHP 8.4+
Laravel 12
Inertia.js
React 19
Vite
TypeScript
Tailwind CSS
Zod for client-side schema validation where needed
React Hook Form or TanStack Form for complex forms
Pest for backend tests
Vitest or Jest plus Testing Library for frontend tests if frontend unit coverage is required
High-Level Responsibilities
Laravel
Routing
Middleware
Authentication and authorization
Validation via Form Requests
Eloquent models and relationships
Services and domain logic
Notifications, jobs, mail, queues
Returning Inertia responses with typed page props
React
Rendering Inertia pages
Local interactivity
Tables, forms, dialogs, filters, tabs, drawers
Progressive enhancement without replacing Laravel routing conventions
Reusable UI component composition
Recommended Project Structure
app/
Actions/
Data/
Http/
Controllers/
Web/
Middleware/
Requests/
Resources/
Jobs/
Models/
Notifications/
Policies/
Providers/
Services/
Support/
resources/
js/
app.tsx
pages/
auth/
dashboard/
settings/
users/
components/
ui/
layout/
forms/
tables/
feedback/
layouts/
hooks/
lib/
types/
utils/
routes/
actions/
schemas/
css/
app.css
views/
app.blade.php
routes/
web.php
auth.php if needed
admin.php if needed
tests/
Feature/
Unit/
Frontend Bootstrapping
The frontend entry point should be an Inertia React app initialized from resources/js/app.tsx. The Blade root view should only contain the app shell and Vite assets.
Recommended initialization responsibilities:
createInertiaApp setup
resolve pages dynamically from resources/js/pages
attach global providers such as theme, toast, and query client only if needed
set document title pattern consistently
use a shared root layout pattern for authenticated and guest pages
Page Organization
Each page should map cleanly from Laravel route to Inertia page component.
Example page organization:
resources/js/pages/dashboard/index.tsx
resources/js/pages/users/index.tsx
resources/js/pages/users/show.tsx
resources/js/pages/settings/profile.tsx
Use shared layouts:
resources/js/layouts/authenticated-layout.tsx
resources/js/layouts/guest-layout.tsx
This keeps page files focused on content while navigation, header, sidebar, flash messaging, and shell concerns stay centralized.
Backend Route and Controller Pattern
Use standard Laravel web routes and controllers returning Inertia pages.
Recommended route pattern:
named routes only
route model binding
middleware groups for auth and role-based access
controller methods returning Inertia::render(...)
Example responsibilities:
index: list data and filters
create: load create page dependencies
store: validate through Form Request, persist through service or model action, redirect with flash
show: return detailed page data
edit: return existing entity plus option lists
update: validate and persist
destroy: authorize and delete, redirect with flash message
Validation Strategy
Use Form Request classes for all meaningful mutations.
Recommended structure:
app/Http/Requests/User/StoreUserRequest.php
app/Http/Requests/User/UpdateUserRequest.php
Validation rules should stay on the server as the source of truth. If client-side validation is added for UX, mirror only the necessary subset with Zod and do not let it replace server validation.
Data Delivery Pattern
Use Inertia page props as the main data contract. Keep props intentional and small.
Recommended data categories:
page data
filter options
pagination meta
auth/user context
flash messages
permissions/capabilities
small UI bootstrap config
Avoid:
dumping entire model graphs
sending unused option collections
duplicating the same data in every response
client-side refetches for data that already exists in the initial page payload
Use Eloquent resources or data objects when shape control matters.
Domain Logic Pattern
Do not place business logic directly in controllers.
Preferred layering:
controllers orchestrate request, authorization, response
Form Requests validate
services or actions handle domain workflows
models define relationships and local model behavior
policies handle authorization rules
This keeps the code maintainable when the app grows beyond CRUD.
Frontend Component Strategy
Use React pages for screen-level composition and a shared component layer for reuse.
Recommended component groups:
components/ui for base primitives
components/layout for shell pieces
components/forms for field wrappers and reusable controls
components/tables for grids, filters, pagination
components/feedback for alerts, empty states, loaders, confirmations
For a new project, choose one UI strategy and keep it consistent:
shadcn/ui if the team wants registry-driven components
or a smaller internal component layer if the project is intentionally lightweight
Do not mix multiple UI paradigms early.
Form Handling
For simple forms:
use Inertia useForm
For complex forms:
use React Hook Form or TanStack Form
use shared field components
map Laravel validation errors cleanly into the form UI
keep submit behavior Inertia-native when possible
Recommended behavior:
optimistic UX only where safe
disable submit during processing
show inline field errors from Laravel
redirect after success rather than manual client mutation when the action changes page state
Authorization
Keep authorization Laravel-first:
Gates and Policies for domain actions
middleware for route-level protection
expose only minimal permission flags to the frontend
Frontend checks should only improve UX, not enforce security.
Authentication
Use Laravel authentication patterns that fit the product:
session-based auth for standard web apps
Sanctum only when API or SPA token-based behavior is genuinely needed
For most Inertia apps, standard Laravel session auth is enough and simpler.
Shared Data
Use Inertia shared props for cross-cutting data:
authenticated user summary
flash messages
app name
locale
feature flags if needed
unread notification count if lightweight
Keep shared props small because they are included on many requests.
Table and List Pattern
For admin and business apps, define a repeatable table pattern:
controller handles filtering, sorting, pagination
request object validates filter inputs
query builder logic stays in a dedicated filter/query class if it grows
page renders a reusable table component
rows are derived from a stable server payload
This avoids inconsistent client-side data logic across screens.
Performance Strategy
keep first load server-driven through Laravel and Inertia
eager load relationships intentionally to avoid N+1 issues
paginate lists
avoid over-fetching page props
defer heavy frontend libraries unless a route truly needs them
split complex UI into reusable components without over-abstracting
queue slow work such as imports, exports, notifications, and third-party sync jobs
Testing Strategy
Backend
Use Pest feature tests for:
page access
auth and policy enforcement
validation behavior
mutation flows
redirects and flash messages
expected Inertia component rendering and props
Typical coverage:
guests are redirected
authorized users can access
invalid payloads fail correctly
valid submissions persist data
policy restrictions return forbidden responses
Frontend
Use Testing Library for:
component rendering
form states
interaction behavior
conditional UI fragments
Do not overtest simple presentational wrappers.
Implementation Phases
Phase 1: Foundation
install Laravel
install Inertia server adapter
install React and TypeScript
configure Vite
create app Blade shell
create Inertia entrypoint
add base layout components
set up Tailwind
configure auth
Phase 2: Core App Shell
authenticated layout
guest layout
header
sidebar or top nav
flash message system
error pages
shared props middleware
Phase 3: First Feature Vertical Slice
Implement one complete feature end-to-end:
migration
model
factory
policy
form requests
controller
routes
Inertia pages
reusable form/table components
tests
This validates the architecture before scaling.
Phase 4: Reusable Patterns
data tables
filters
modal confirmations
form field system
empty states
notifications
settings pages
pagination pattern
Phase 5: Operational Hardening
queue workers
notifications
activity logging if needed
import/export jobs
audit trail
production build pipeline
CI for tests and linting
Recommended Engineering Rules
controllers stay thin
validation always uses Form Requests
policies guard sensitive actions
Eloquent relationships use explicit types and eager loading
no raw query shortcuts unless the query is truly complex
no frontend-only source of truth for protected business rules
page props remain small and intentional
each major mutation path gets a feature test
route names are stable and used consistently in redirects and links
Minimal Starter Feature Example
A good first feature for proving the stack is “Projects” or “Teams”:
list page with filters and pagination
create page with validation
edit page with policy checks
details page with related records
delete flow with confirmation
role-aware actions
feature tests for access and mutations
That is enough to validate the full Laravel Inertia React architecture.
Outcome
This implementation gives you:
Laravel-native backend workflows
React-powered pages without a separate SPA API layer
simpler auth and routing than a decoupled frontend
strong maintainability through predictable structure
room to scale into a serious business application without re-platforming


# Technical Spec Template

> Fill only the fields applicable to the task. If not relevant, leave out of the criteria.

---

## What Actions

**Q: Name the `app/{Domain Folder}/Actions` or `app/{Domain Folder}/Services` classes created.**
- Briefly describe the single responsibility or business logic executed.

## What Models

**Q: List the new or updated `app/{Domain Folder}/Models` classes.**
- Specify added relationships (`hasMany`, etc.) and fillable properties.

## What Migrations

**Q: Name the new tables or columns added in `database/migrations`.**
- Note any required indexing, unique constraints, or foreign keys.

## Validation & DTOs

**Q: List the Form Requests enforcing validation rules.**
- `app/Http/Requests` or `app/{Domain Folder}/Requests`

**Q: List the DTO classes created to strictly type the validated incoming data.**
- `app/{Domain Folder}/DTOs`

## Routes & Controllers

**Q: Define the HTTP verb and endpoint path.**
- e.g., `POST /api/resource`
- Specify the target Controller method and attached middleware (e.g., `auth:sanctum`)

## API Resources

**Q: Name the API Resource classes created to format the outgoing JSON response.**
- `app/Http/Resources` or `app/{Domain Folder}/Resources`

## Policies & Authorization

**Q: Name the classes created in `app/{Domain Folder}/Policies` enforcing business rules or model authorization.**
- Define the specific user roles or conditions required to pass.

## Queries

**Q: Name the classes handling complex database retrieval or external API fetching.**
- `app/{Domain Folder}/Queries`

## Events & Listeners

**Q: List the internal Domain Events triggered by the Actions.**
- `app/{Domain Folder}/Events`

**Q: List the Event Listeners reacting to those events.**
- `app/{Domain Folder}/Listeners`

## Jobs

**Q: List the background Jobs reacting to Domain Events or handling heavy processing.**
- `app/{Domain Folder}/Jobs`
- Specify the queue connections/names.

## Mail & Notifications

**Q: Name the Mailables or Notification classes handling external communication.**

## Commands

**Q: Name the new Artisan commands created in `app/Console/Commands`.**
- List the command signature and its scheduled frequency if applicable.

## Tests

**Q: List the Feature or Unit tests created.**
- Specify the exact scenarios being covered (e.g., "asserts 422 on invalid email").

## Environment & Config

**Q: List any new variables that need to be added to `.env` and `.env.example`.**

## Edge Cases & Notes

**Q: List any potential points of failure, race conditions, or required background jobs.**
- Note specific payload conditions, third-party API limits, or tricky scenarios the reviewer should test.

What Actions:
Name the app/{Domain Folder}/Actions or app/{Domain Folder}/Services classes created.
Briefly describe the single responsibility or business logic executed.
What Models:
List the new or updated app/{Domain Folder}/Models classes.
Specify added relationships (hasMany, etc.) and fillable properties.
What Migrations:
Name the new tables or columns added in database/migrations.
Note any required indexing, unique constraints, or foreign keys.
Validation & DTOs:
List the Form Requests (app/Http/Requests or app/{Domain Folder}/Requests) enforcing validation rules.
List the classes created in app/{Domain Folder}/DTOs to strictly type the validated incoming data.
Routes & Controllers:
Define the HTTP verb and endpoint path (e.g., POST /api/resource).
Specify the target Controller method and attached middleware (e.g., auth:sanctum).
API Resources (If applicable):
Name the API Resource classes created to format the outgoing JSON response (app/Http/Resources or app/{Domain Folder}/Resources).
Policies & Authorization:
Name the classes created in app/{Domain Folder}/Policies enforcing business rules or model authorization.
Define the specific user roles or conditions required to pass.
Queries:
Name the classes handling complex database retrieval or external API fetching (app/{Domain Folder}/Queries).
Events & Listeners:
List the internal Domain Events triggered by the Actions (app/{Domain Folder}/Events).
List the Event Listeners reacting to those events (app/{Domain Folder}/Listeners).
Jobs:
List the background Jobs reacting to Domain Events or handling heavy processing (app/{Domain Folder}/Jobs).
Specify the queue connections/names.
Mail & Notifications:
Name the Mailables or Notification classes handling external communication 
Commands:
Name the new Artisan commands created in app/Console/Commands.
List the command signature and its scheduled frequency if applicable.
Tests:
List the Feature or Unit tests created
Specify the exact scenarios being covered (e.g., "asserts 422 on invalid email").
Environment & Config:
List any new variables that need to be added to .env and .env.example.
Edge Cases & Notes:
List any potential points of failure, race conditions, or required background jobs.
Note specific payload conditions, third-party API limits, or tricky scenarios the reviewer should test.

# Acceptance Criteria Template

> Fill only the fields applicable to the task. If not relevant, leave out of the criteria.

**Example task:** Integrate Cloudflare Turnstile into the registration form of SelfieCash.

---

## Client-side

### Layout

**Q: Is there a layout design provided?**
- \<link to the Figma design\>

### Positioning

**Q: Where is the relevant interactable element positioned?**
- The Turnstile widget should appear at the end of the form

### Screen-size Friendliness

**Q: Is the element supposed to adapt according to the screen size?**
- Mobile-first

### Behavior

**Q: How is the element expected to behave when in different screen sizes?**
- The widget should stretch and fill the available horizontal space
- The widget's theme should adapt according to the site theme of either dark or light

### Validation

**Q: Should an error occur, what is expected to be seen and where?**
- There should be a human-readable error text message in the lower left-side
- Error message should be formatted similarly to other error messages on the form

---

## Server-side

### Side-effects

**Q: List down all known effects to data.**
- Upon registration, the Turnstile token should be required and evaluated if valid or not by Cloudflare's API
- If invalid, a custom human-readable error message must be thrown
- If valid, the registration process proceeds to the next step

Project: Newcomer Navigation — Frontend Development
Transform the project concept Newcomer Navigation into a complete, polished, multi-page, locally runnable web application for students, staff, and other members of the Bennett University, Greater Noida community.

1. Scope and development requirements
Build the entire frontend first. This phase is exclusively for UI/UX, page structure, reusable components, frontend interactions, and a clean project structure that can later be connected to a backend.

Assume that no existing application, backend, database, API, or codebase exists. Start from scratch.

Requirements:

Create a multi-page web application, not a single static landing page.
Make the application suitable for local development and hosting.
Use a consistent, reusable design system.
Implement all navigation, forms, filters, voting controls, chat interactions, and profile interactions as functional frontend experiences.
Use realistic mock data and local demo state wherever persistent backend functionality is not yet available.
Clearly separate mock data and temporary frontend logic from the actual future backend integration.
Do not pretend that authentication, email verification, database storage, or AI API calls are real when they are not connected.
Organize the project into clean, maintainable, multi-file components and pages.
Use React with TypeScript and Vite if supported. Otherwise, use a modern, maintainable frontend framework that supports local development.
Use responsive layouts that work on desktop, tablet, and mobile.
Include appropriate loading, empty, error, success, and validation states.
The result should feel like a real university community platform, not a generic AI-generated template.

2. Product identity and visual direction
The product is called Newcomer Navigation.

It helps newcomers find answers, understand university life, connect with the community, and navigate Bennett University.

Create a polished, modern, welcoming, trustworthy interface. The visual direction should combine:

A clean, contemporary university portal.
A friendly community Q&A platform.
A helpful AI assistant as the primary product feature.
Use a coherent color palette, typography, spacing system, icons, cards, borders, and interaction states.

Avoid excessive gradients, cluttered dashboards, generic stock-photo-heavy layouts, oversized decorative elements, and unnecessary animations.

The UI should prioritize clarity, accessibility, and ease of navigation.

Choose a suitable logo/wordmark and a simple placeholder brand identity if necessary.

3. Global navigation
Create a persistent top navigation bar with easy access to all major pages:

Home / Sign in
Forum
Chatbot
Profile
Include a logo or wordmark that links to Home.

When a user is signed in, show their generated username or first name and a profile/avatar menu.

When signed out, show appropriate Sign in and Sign up actions.

Make the navigation responsive. On smaller screens, use a suitable mobile menu.

Highlight the currently active page.

All pages must be accessible through the navigation, including when the user is signed out. Where a feature requires authentication, show a clear, friendly sign-in prompt rather than a broken page.

4. Home page — Sign in, sign up, and overview
Create a simple, attractive home page with authentication as its primary purpose.

The page should contain:

A welcoming headline and short description of Newcomer Navigation.
A sign-in / sign-up interface.
A brief overview of the site's features underneath or alongside the authentication area.
A clear explanation of how the platform helps students and staff find answers.
Keep the page relatively simple and uncluttered.

Sign-up requirements
Provide a registration form with the following fields:

Full name.
Phone number, required.
Email address, required.
Account type: Student, Staff, or Other.
Password.
Re-enter password.
Requirements:

The username must be automatically generated from the user's full name rather than chosen manually.
Display the generated username in the registration interface.
Handle duplicate names gracefully, with a predictable username suffix strategy.
Validate required fields and appropriate email and phone formats.
Require passwords to match.
Include basic password-strength guidance and show/hide password controls.
Provide clear inline validation messages.
Include an appropriate consent/terms acknowledgement if needed.
Do not expose passwords in the interface or logs.
Student and staff verification
For Student and Staff registrations, include a verification step using the appropriate university email address.

The UI should clearly distinguish:

Student verification.
Staff verification.
Other account registration.
Allow a verification-code or verification-link flow to be represented in the frontend.

Since no backend exists yet, verification must be a clearly labeled demo experience, not a claim of real email delivery or identity verification.

Make the UI ready for a future backend to enforce institutional email domains and verification.

Sign-in requirements
Include:

Email or generated username.
Password.
Show/hide password.
Remember-me option if appropriate.
Forgot password entry point.
Helpful validation and error states.
A link to switch to sign-up.
Create a polished authentication experience that is easy to use and does not overwhelm newcomers.

5. Forum — Community Q&A
Build a complete forum experience where students, staff, and other community members can ask questions, answer them, and discover useful information.

Forum landing page
Include:

A prominent search bar.
A clear Ask a Question action.
Question cards with title, short preview, author, profile avatar, date, tags, answer count, and voting/activity information.
Sorting options such as Latest, Most Upvoted, and Most Answered.
Filters by academic stream/course and non-academic category.
A clear distinction between questions that are answered and unanswered.
Academic and non-academic filters
Provide course/stream filters for Bennett University, Greater Noida, including relevant programmes such as:

B.Tech.
BCA.
Mass Communication.
M.Tech.
Other undergraduate and postgraduate programmes.
Also provide non-academic categories such as:

Hostel.
Campus life.
Sports.
Clubs and societies.
Events.
Transport.
Food.
Facilities.
General university questions.
Do not assume that this list is a verified, exhaustive list of Bennett University programmes. Keep categories and programmes configurable so that the actual official course list can be added later.

Support combinations of filters and a way to clear them.

Ask a question
Provide a form or modal with:

Question title.
Detailed description.
Academic stream/course or general category.
Relevant tags.
Submit and cancel actions.
Validate required fields and show a successful frontend demo submission.

Individual question and answer thread
Clicking a question should open a dedicated thread page or detailed view.

Show:

Full question and description.
Author's profile link.
Date posted.
Tags and category.
All answers.
Answer author profiles.
Upvote and downvote controls.
Answer submission form.
Reply functionality where appropriate.
Sort answers by highest net vote score by default, with a way to switch to Latest.

Ensure voting interactions visibly update the UI. A user should not be able to vote repeatedly in a way that produces inconsistent demo state.

Make the interaction model ready for authenticated, server-side voting later.

Forum profile navigation
Clicking any question or answer author's name or avatar must navigate to that user's public profile.

Provide realistic mock questions, answers, authors, and vote counts to make the forum feel populated during the frontend demo.

6. User profiles
Create a dedicated profile page for every user, including a realistic example profile.

The profile should display:

Profile picture placeholder.
Full name.
Automatically generated username.
Account type: Student, Staff, or Other.
Student/staff verification badge when applicable.
Course, stream, or department where applicable.
About/bio section.
Date joined.
Total questions asked.
Total answers given.
Total upvotes received.
Other useful community activity.
Include tabs or sections for:

Overview.
Questions.
Answers.
Activity, if appropriate.
Profile ownership and editing
When viewing your own profile:

Show an edit button beside the profile picture.
Show an edit button beside the About section.
Allow editing relevant profile information.
Allow the owner to update their profile picture placeholder or choose a local demo image if supported.
When viewing someone else's profile:

Do not display the owner's edit controls.
Show only public profile information and public activity.
Use frontend demo identity state to distinguish the current user from other users. Do not treat this as real authorization.

7. Main feature — Chatbot
Create a polished, dedicated chatbot page. This is the central feature of Newcomer Navigation and should receive the most design attention.

Suggested name: Navi — Your Newcomer Assistant.

The chatbot should feel friendly, intelligent, helpful, and specifically designed for Bennett University newcomers.

Chat interface
Include:

A welcoming first message.
A personalized greeting using the signed-in user's first name.
A clean conversation layout.
Message bubbles with clear visual distinction between user and assistant.
A message input field.
Send button.
Enter-to-send support.
Typing/loading indicator.
Suggested starter questions.
Clear conversation action.
Helpful error and fallback states.
Responsive mobile layout.
Example suggested questions:

"How do I find my department?"
"What should I know before moving into the hostel?"
"Where can I find information about campus facilities?"
"How do I get help with university-related questions?"
Frontend-only chatbot behavior
For this phase, create a realistic demo chatbot using clearly labeled mock responses or a small mock knowledge base.

Do not claim that it is already connected to an AI API, university database, or forum database.

Prepare a clean frontend service interface so that a real backend chatbot can replace the demo implementation later without redesigning the chat UI.

The future chatbot must support the following response priority:

Search approved university data and the application's knowledge base first.
If the information is not available, search the forum for an exact or similar question and use the highest-rated relevant answer.
If neither source provides a sufficiently relevant answer, provide a generic response and clearly advise the user to contact Bennett University, Greater Noida, for authoritative details.
The chatbot must not invent university policies, deadlines, fees, facilities, or other institution-specific facts.

When the answer is based on a forum response, the future implementation should be able to show the source question, answer author, and a link to the original thread.

For the frontend demo, make the source of each response visually identifiable, such as:

University information.
Community answer.
General guidance.
Personalization
Use the signed-in user's first name in assistant greetings and conversational responses.

If no user is signed in, use a neutral greeting and provide a sign-in prompt where personalization is useful.

Do not hardcode one user's name into the chatbot.

8. Mock data and frontend interactions
Create realistic, centralized mock data for:

Users.
Courses and streams.
Categories and tags.
Questions.
Answers.
Votes.
User activity.
Chat messages.
Demo knowledge-base entries.
Ensure all pages use consistent user identities and question IDs.

Implement frontend demo interactions for:

Switching between sign-in and sign-up.
Generating a username from a full name.
Form validation.
Switching between account types.
Filtering and searching forum questions.
Sorting questions and answers.
Opening question threads.
Submitting demo questions and answers.
Upvoting and downvoting.
Navigating between profiles.
Editing the current user's profile.
Sending chatbot messages and showing demo responses.
Use local state or local demo persistence only where appropriate. Clearly identify anything that will require a real backend.

9. Accessibility and UX quality
Ensure:

Accessible labels and keyboard navigation.
Visible focus states.
Good text contrast.
Responsive layouts.
Readable typography.
Clear form errors.
Helpful empty states.
Consistent button behavior.
Appropriate loading indicators.
No dead-end navigation.
No nonfunctional controls presented as working features.
Use confirmation dialogs for potentially destructive actions where appropriate.

10. Code structure and future backend integration
Organize the frontend into maintainable files and reusable components.

A suggested structure:

src/pages/ — Home, Forum, QuestionThread, Profile, Chatbot.
src/components/ — Navigation, cards, forms, voting, chat components, profile components.
src/data/ — Mock users, questions, answers, categories, demo knowledge base.
src/services/ — Frontend service interfaces and mock implementations.
src/types/ — Shared TypeScript models.
src/ — Application entry point, routing, styles, and configuration.
Adapt this structure as needed, but preserve clear separation of concerns.

Prepare service interfaces for future:

Authentication.
Email verification.
User profiles.
Forum questions and answers.
Voting.
Chatbot requests.
University knowledge-base retrieval.
Do not implement a real backend in this phase.

Avoid tightly coupling UI components to mock data. The backend should later be able to replace mock service implementations without requiring a frontend redesign.

11. Completion requirements
Deliver the complete frontend project, not just screenshots or a visual mockup.

Before finishing:

Ensure every major page exists.
Ensure navigation works.
Ensure the core demo interactions work.
Ensure the application runs locally.
Include all required source files and dependencies.
Include clear instructions for installing dependencies and starting the local development server.
Identify any unfinished frontend behavior.
Identify which features are demo-only and will require backend integration.
Final goal: A polished, cohesive, responsive Newcomer Navigation frontend that is ready to be copied into a repository and connected to a separately developed backend, without redesigning or replacing the frontend.
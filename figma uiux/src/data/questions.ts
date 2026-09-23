import type { Question, Answer } from '../types';

export const MOCK_QUESTIONS: Question[] = [
  {
    id: 'q1',
    title: 'How does the hostel room allocation work for freshers?',
    body: `I'm joining B.Tech CSE this year and I'm really confused about the hostel process. A few things I want to know:
1. Is hostel compulsory for first-year students?
2. How are rooms allocated — is it random or can we request specific blocks?
3. What should I bring and what's already provided?
4. Are there any specific rules about guests and visiting hours?

Any help from seniors who've been through this would be amazing!`,
    authorId: 'u7',
    categoryId: 'hostel',
    tags: ['hostel', 'admission'],
    createdAt: '2024-08-05T09:30:00Z',
    updatedAt: '2024-08-07T14:20:00Z',
    answerCount: 3,
    upvotes: 24,
    downvotes: 1,
    isAnswered: true,
    views: 312,
  },
  {
    id: 'q2',
    title: 'What programming languages are taught in B.Tech CSE first year?',
    body: `I'm about to start B.Tech CSE and I want to prepare in advance. Which programming languages will we cover in the first year? Should I start learning Python, C, or Java beforehand? Is there any recommended prep material from the department?`,
    authorId: 'u7',
    categoryId: 'btech',
    tags: ['coding', 'exam'],
    createdAt: '2024-08-06T11:00:00Z',
    updatedAt: '2024-08-08T10:45:00Z',
    answerCount: 4,
    upvotes: 31,
    downvotes: 0,
    isAnswered: true,
    views: 428,
  },
  {
    id: 'q3',
    title: 'Is there a shuttle service from Greater Noida metro station to campus?',
    body: `I'll be commuting daily from Sector 62, Noida. Is there an official university shuttle that connects the campus to the nearest metro station? What are the timings and is there a fee for it? Any alternatives like shared autos or cabs that are popular among students?`,
    authorId: 'u5',
    categoryId: 'transport',
    tags: ['transport'],
    createdAt: '2024-08-04T08:15:00Z',
    updatedAt: '2024-08-06T16:30:00Z',
    answerCount: 2,
    upvotes: 18,
    downvotes: 0,
    isAnswered: true,
    views: 267,
  },
  {
    id: 'q4',
    title: 'How do I apply for the Times Bennett scholarship?',
    body: `I've heard Bennett University has the Times Bennett scholarship for meritorious students. Can someone explain the eligibility criteria, application process, and when the applications open? Does it apply only to incoming students or can existing students apply too?`,
    authorId: 'u7',
    categoryId: 'general',
    tags: ['scholarship', 'fees'],
    createdAt: '2024-08-03T14:00:00Z',
    updatedAt: '2024-08-05T09:10:00Z',
    answerCount: 2,
    upvotes: 42,
    downvotes: 0,
    isAnswered: true,
    views: 589,
  },
  {
    id: 'q5',
    title: 'What clubs and societies are active on campus this year?',
    body: `I'm interested in joining technical and cultural clubs. What are the most active clubs at Bennett University? When do they hold auditions or recruitment drives? Is there a centralised list somewhere? I'm particularly interested in coding, music, and debate.`,
    authorId: 'u5',
    categoryId: 'clubs',
    tags: ['clubs', 'events'],
    createdAt: '2024-08-07T16:45:00Z',
    updatedAt: '2024-08-09T11:00:00Z',
    answerCount: 5,
    upvotes: 37,
    downvotes: 1,
    isAnswered: true,
    views: 450,
  },
  {
    id: 'q6',
    title: 'How is the Wi-Fi coverage on campus and in hostels?',
    body: `Is the campus Wi-Fi reliable for video calls and coding work? Does it extend to hostel rooms or is there a separate network there? Any tips for getting the best connectivity?`,
    authorId: 'u4',
    categoryId: 'facilities',
    tags: ['wifi', 'facilities'],
    createdAt: '2024-08-08T10:20:00Z',
    updatedAt: '2024-08-08T18:00:00Z',
    answerCount: 3,
    upvotes: 15,
    downvotes: 2,
    isAnswered: true,
    views: 201,
  },
  {
    id: 'q7',
    title: 'What is the grading system and how are internal marks calculated?',
    body: `I want to understand how the CGPA system works at Bennett. What is the grading scale? How much weight do internal assessments carry compared to end-semester exams? Is attendance factored into the grade?`,
    authorId: 'u7',
    categoryId: 'btech',
    tags: ['exam', 'faculty'],
    createdAt: '2024-08-09T09:00:00Z',
    updatedAt: '2024-08-10T12:30:00Z',
    answerCount: 2,
    upvotes: 28,
    downvotes: 0,
    isAnswered: false,
    views: 334,
  },
  {
    id: 'q8',
    title: 'Are there any internship placement resources for BCA students?',
    body: `I'm a BCA second-year student looking for internship opportunities. Does the placement cell at Bennett help BCA students too, or is it only for B.Tech? What resources are available for finding summer internships?`,
    authorId: 'u2',
    categoryId: 'bca',
    tags: ['internship', 'placement'],
    createdAt: '2024-08-10T13:00:00Z',
    updatedAt: '2024-08-10T13:00:00Z',
    answerCount: 0,
    upvotes: 9,
    downvotes: 0,
    isAnswered: false,
    views: 112,
  },
  {
    id: 'q9',
    title: 'What food options are available on campus?',
    body: `Is the mess food good? Are there separate mess options for vegetarians? Are there any other canteens, food courts, or food delivery options available on or near campus?`,
    authorId: 'u7',
    categoryId: 'food',
    tags: ['mess', 'food'],
    createdAt: '2024-07-30T11:00:00Z',
    updatedAt: '2024-08-02T15:40:00Z',
    answerCount: 6,
    upvotes: 54,
    downvotes: 1,
    isAnswered: true,
    views: 703,
  },
  {
    id: 'q10',
    title: 'How do I get a Bennett University student ID card?',
    body: `When and where do I collect my student ID card? Is it issued automatically after admission or do I need to apply separately? What documents do I need?`,
    authorId: 'u5',
    categoryId: 'general',
    tags: ['admission'],
    createdAt: '2024-07-28T08:30:00Z',
    updatedAt: '2024-07-29T12:00:00Z',
    answerCount: 3,
    upvotes: 21,
    downvotes: 0,
    isAnswered: true,
    views: 278,
  },
];

export const MOCK_ANSWERS: Answer[] = [
  // Answers for q1 — hostel room allocation
  {
    id: 'a1',
    questionId: 'q1',
    body: `Hey! Welcome to Bennett. Here's what I know from my own first year experience:

**Hostel allocation**: Hostel is not compulsory but it is heavily encouraged for first-year students. Rooms are allocated by the hostel administration, usually based on your course and year. You can submit a roommate preference form, but it's not always guaranteed.

**What's provided**: Each room comes with a bed, mattress, study table, chair, and wardrobe. You need to bring your own bedsheets, pillow covers, and towels. A bucket and mug are also your responsibility.

**Visiting hours**: Guests are allowed in the common areas until 8 PM on weekdays. Opposite-gender visitors are generally not allowed in room corridors.

Feel free to ask more — happy to help!`,
    authorId: 'u1',
    createdAt: '2024-08-05T14:30:00Z',
    updatedAt: '2024-08-05T14:30:00Z',
    upvotes: 18,
    downvotes: 0,
    isAccepted: true,
  },
  {
    id: 'a2',
    questionId: 'q1',
    body: `Adding to the above — one practical tip: reach the campus on the first day of hostel check-in early if you want a better pick of rooms in your block. The allocation is done on a first-come basis within your assigned block. Also, make sure to carry a lock for your wardrobe!`,
    authorId: 'u2',
    createdAt: '2024-08-06T09:15:00Z',
    updatedAt: '2024-08-06T09:15:00Z',
    upvotes: 11,
    downvotes: 0,
    isAccepted: false,
  },
  {
    id: 'a3',
    questionId: 'q1',
    body: `The hostel warden office is very approachable. If you have any specific needs or concerns (health-related room requirements, for example), you can speak directly to them during check-in. They're usually accommodating for first-year students.`,
    authorId: 'u6',
    createdAt: '2024-08-07T10:00:00Z',
    updatedAt: '2024-08-07T10:00:00Z',
    upvotes: 7,
    downvotes: 0,
    isAccepted: false,
  },
  // Answers for q2 — programming languages
  {
    id: 'a4',
    questionId: 'q2',
    body: `In B.Tech CSE first year at Bennett, the primary language introduced is **C**. You'll learn data structures and algorithms in C during the first semester. Python is introduced in the second semester as part of a programming lab. Java comes later, typically in second year.

My recommendation: get comfortable with C basics — variables, loops, arrays, functions, and pointers. That foundation will help you immensely.`,
    authorId: 'u1',
    createdAt: '2024-08-06T15:00:00Z',
    updatedAt: '2024-08-06T15:00:00Z',
    upvotes: 24,
    downvotes: 0,
    isAccepted: true,
  },
  {
    id: 'a5',
    questionId: 'q2',
    body: `Dr. Suresh's recommendation to the batch last year was to spend the summer doing basic C programming — specifically arrays, strings, and pointer arithmetic. If you're already comfortable with Python, that's great, but C is what you'll be formally assessed on in Semester 1.`,
    authorId: 'u3',
    createdAt: '2024-08-07T08:30:00Z',
    updatedAt: '2024-08-07T08:30:00Z',
    upvotes: 30,
    downvotes: 0,
    isAccepted: false,
  },
  {
    id: 'a6',
    questionId: 'q2',
    body: `The competitive coding club — ACM Student Chapter — also runs a beginner bootcamp in the first week of college. It's free and a great way to meet peers. Keep an eye out for the announcement on the official student portal.`,
    authorId: 'u6',
    createdAt: '2024-08-08T11:00:00Z',
    updatedAt: '2024-08-08T11:00:00Z',
    upvotes: 15,
    downvotes: 1,
    isAccepted: false,
  },
  {
    id: 'a7',
    questionId: 'q2',
    body: `I'd suggest also looking at HackerRank's "30 Days of Code" challenge. It's language-agnostic and gets you thinking algorithmically, which matters more than any specific language in first year.`,
    authorId: 'u2',
    createdAt: '2024-08-08T16:20:00Z',
    updatedAt: '2024-08-08T16:20:00Z',
    upvotes: 9,
    downvotes: 0,
    isAccepted: false,
  },
  // Answers for q9 — food
  {
    id: 'a8',
    questionId: 'q9',
    body: `The campus has a central mess that serves breakfast, lunch, and dinner. The food is decent — not restaurant quality but filling and hygienic. There are separate vegetarian and non-vegetarian options at every meal.

Apart from the mess, there's a food court in the campus centre with options like South Indian, Chinese, sandwiches, and beverages. Zomato and Swiggy deliver to the campus gates too, and a few popular chains like Domino's have outlets in the nearby Galgotia market (a 10-minute auto ride).`,
    authorId: 'u1',
    createdAt: '2024-07-31T10:30:00Z',
    updatedAt: '2024-07-31T10:30:00Z',
    upvotes: 35,
    downvotes: 0,
    isAccepted: true,
  },
  {
    id: 'a9',
    questionId: 'q9',
    body: `The mess timings are strict — missing breakfast or lunch usually means you have to wait for the next meal unless the food court is open. Pro tip: the paratha counter at the food court is the best thing on campus. Highly recommended.`,
    authorId: 'u5',
    createdAt: '2024-07-31T14:00:00Z',
    updatedAt: '2024-07-31T14:00:00Z',
    upvotes: 21,
    downvotes: 0,
    isAccepted: false,
  },
  // Answers for q4 — scholarship
  {
    id: 'a10',
    questionId: 'q4',
    body: `The Times Bennett Scholarship is one of the flagship scholarships at the university. It covers a significant portion of tuition fees for high-performing students. The eligibility typically includes:
- Minimum 85% in Class 12 (for incoming students)
- High JEE Main / SAT / board scores
- Demonstrated leadership or extracurricular achievement

Applications open before the academic year begins. Keep an eye on the official Bennett University website and the admissions office communications. Existing students may apply for merit scholarships based on CGPA after their first semester results.`,
    authorId: 'u3',
    createdAt: '2024-08-03T16:00:00Z',
    updatedAt: '2024-08-03T16:00:00Z',
    upvotes: 38,
    downvotes: 0,
    isAccepted: true,
  },
  // Answers for q5 — clubs
  {
    id: 'a11',
    questionId: 'q5',
    body: `Some of the most active clubs at Bennett University:
- **Technical**: ACM Student Chapter, IEEE Student Branch, CodeBennett
- **Cultural**: Nukkad Natak (street theatre), BU Music Club, Photography Club
- **Debate & Literary**: Bennett Debate Club, The Literary Society
- **Sports**: Football, Cricket, Badminton, Basketball teams (all have try-outs in August/September)
- **Entrepreneurship**: Bennett's E-Cell

Recruitment drives usually happen in the first month of the new semester. Keep an eye on the official student WhatsApp groups and notice boards in the academic blocks.`,
    authorId: 'u2',
    createdAt: '2024-08-07T18:00:00Z',
    updatedAt: '2024-08-07T18:00:00Z',
    upvotes: 29,
    downvotes: 0,
    isAccepted: true,
  },
];

export function getQuestionById(id: string): Question | undefined {
  return MOCK_QUESTIONS.find(q => q.id === id);
}

export function getAnswersByQuestionId(questionId: string): Answer[] {
  return MOCK_ANSWERS.filter(a => a.questionId === questionId);
}

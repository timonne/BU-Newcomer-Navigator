import type { KnowledgeBaseEntry } from '../types';

// Demo knowledge base — will be replaced by a real backend retrieval service
export const KNOWLEDGE_BASE: KnowledgeBaseEntry[] = [
  {
    id: 'kb1',
    question: 'Where is Bennett University located?',
    answer: 'Bennett University is located in Plot No. 8-11, TechZone II, Greater Noida, Uttar Pradesh - 201310. It is part of the Times of India Group and was established in 2016.',
    keywords: ['location', 'address', 'where', 'greater noida'],
    category: 'General',
    sourceType: 'university',
  },
  {
    id: 'kb2',
    question: 'How do I find my department or academic block?',
    answer: 'Bennett University has a central academic block layout. The Engineering and Computing departments are housed in the main academic building (Block A). The Mass Communication and Media departments are in Block B. The Management block is separate and near the administrative offices. Campus maps are available at the security gate and on the student portal. You can also ask at the reception in the main lobby, which has helpful staff for new students.',
    keywords: ['department', 'block', 'find', 'building', 'academic', 'navigate', 'map', 'location'],
    category: 'Campus Navigation',
    sourceType: 'university',
  },
  {
    id: 'kb3',
    question: 'What should I know before moving into the hostel?',
    answer: 'Before moving into the Bennett University hostel, here is what you need to know: (1) Bring your own bedsheets, pillow covers, towels, and a lock for your wardrobe. The room provides a bed, mattress, study table, chair, and wardrobe. (2) You must submit your ID proof at the hostel office on the day of check-in. (3) Mess registration is separate from hostel registration. (4) Visitors are allowed only in common areas until 8 PM on weekdays. (5) The hostel has 24/7 security. There is a separate girls\' and boys\' hostel on campus.',
    keywords: ['hostel', 'moving in', 'dorm', 'room', 'check-in', 'accommodation', 'stay'],
    category: 'Hostel',
    sourceType: 'university',
  },
  {
    id: 'kb4',
    question: 'What are the campus facilities at Bennett University?',
    answer: 'Bennett University offers a wide range of facilities: (1) Library with digital access and physical books. (2) State-of-the-art computer labs and coding labs. (3) Sports facilities including cricket ground, football field, basketball courts, and a gymnasium. (4) Food court and mess. (5) Wi-Fi across the campus and hostels. (6) Medical centre on campus. (7) ATM and bank branch on campus. (8) Common rooms and recreation areas in hostels.',
    keywords: ['facilities', 'library', 'sports', 'gym', 'medical', 'atm', 'wifi', 'labs', 'campus'],
    category: 'Facilities',
    sourceType: 'university',
  },
  {
    id: 'kb5',
    question: 'How do I get help with university-related questions?',
    answer: 'For any university-related questions, you have several options: (1) Visit the Student Services desk in the main administrative building (open 9 AM – 5 PM, Monday to Friday). (2) Contact your programme coordinator directly — contact details are on the student portal. (3) Post your question on Newcomer Navigation\'s community forum and get help from seniors and staff. (4) For urgent matters, contact the Dean of Students office. (5) For hostel-related issues, the Hostel Warden is available on campus. For authoritative or time-sensitive information, always cross-check with official Bennett University communications.',
    keywords: ['help', 'support', 'contact', 'questions', 'admin', 'services', 'queries'],
    category: 'General',
    sourceType: 'university',
  },
  {
    id: 'kb6',
    question: 'What programmes does Bennett University offer?',
    answer: 'Bennett University offers undergraduate, postgraduate, and doctoral programmes. Undergraduate programmes include B.Tech (CSE, ECE, ME, CE), BCA, B.Sc, B.Com, BBA, Mass Communication, and LLB. Postgraduate programmes include M.Tech, MBA, MCA, M.Sc, and LLM. The university also offers PhD programmes in several disciplines. For the most current and authoritative list of programmes and specialisations, always refer to the official Bennett University website.',
    keywords: ['programmes', 'courses', 'btech', 'mba', 'mca', 'degree', 'study'],
    category: 'Academic',
    sourceType: 'university',
  },
  {
    id: 'kb7',
    question: 'What is the student portal and how do I access it?',
    answer: 'The Bennett University student portal is your central hub for academic information. It contains your timetable, attendance records, grades, fee payment, library access, and official communications from the university. You receive your portal login credentials in your official admission communication. If you have not received them, contact the IT helpdesk in the main academic building or email the IT support team. The portal is accessible from any web browser.',
    keywords: ['portal', 'login', 'student portal', 'access', 'credentials', 'timetable', 'attendance'],
    category: 'Academic',
    sourceType: 'university',
  },
];

export function findKnowledgeBaseMatch(query: string): KnowledgeBaseEntry | null {
  const q = query.toLowerCase();
  let bestMatch: KnowledgeBaseEntry | null = null;
  let bestScore = 0;
  for (const entry of KNOWLEDGE_BASE) {
    const score = entry.keywords.filter(k => q.includes(k)).length;
    if (score > bestScore) {
      bestScore = score;
      bestMatch = entry;
    }
  }
  return bestScore > 0 ? bestMatch : null;
}

export const SUGGESTED_QUESTIONS = [
  'How do I find my department?',
  'What should I know before moving into the hostel?',
  'Where can I find information about campus facilities?',
  'How do I get help with university-related questions?',
  'What courses does Bennett University offer?',
  'How do I access the student portal?',
];

export const FALLBACK_RESPONSES = [
  "I don't have specific information about that yet. For authoritative details, please contact the Bennett University Student Services desk or visit the official website. You could also post your question on the Newcomer Navigation forum — seniors and staff are very helpful!",
  "That's a great question, but I want to make sure you get accurate information. I'd recommend checking with the relevant department directly or posting on the community forum where students and staff can give you a verified answer.",
  "I'm still learning about all the specifics of Bennett University. For this query, please reach out to the Student Services office (Main Admin Building, 9 AM – 5 PM) or the Newcomer Navigation forum for a reliable answer.",
];

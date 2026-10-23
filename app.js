const languageSelect = document.querySelector("#language-select");
const authScreen = document.querySelector("#auth-screen");
const appShell = document.querySelector("#app-shell");
const registerForm = document.querySelector("#register-form");
const loginForm = document.querySelector("#login-form");
const authStatus = document.querySelector("#auth-status");
const aiConsentCheckbox = document.querySelector("#ai-consent-checkbox");
const profileForm = document.querySelector("#profile-form");
const profileStatus = document.querySelector("#profile-status");
const aiReportSummary = document.querySelector("#ai-report-summary");
const greetingElement = document.querySelector("#greeting");
const greetingTimeElement = document.querySelector("#greeting-time");
const dateElement = document.querySelector("#today-date");
const chatLog = document.querySelector("#chat-log");
const messageForm = document.querySelector("#message-form");
const messageInput = document.querySelector("#message-input");
const sendButton = messageForm.querySelector("button[type='submit']");
const consentCheckbox = document.querySelector("#consent-checkbox");
const statusMessage = document.querySelector("#status-message");
const clearButton = document.querySelector("#clear-conversation");
const activityOptions = document.querySelector(".activity-options");
const activityPlay = document.querySelector("#activity-play");
const activityIntro = document.querySelector("#activity-intro");
const recallForm = document.querySelector("#recall-form");
const activityResult = document.querySelector("#activity-result");
const wordDisplay = document.querySelector("#word-display");
const spatialGrid = document.querySelector("#spatial-grid");
const symbolGame = document.querySelector("#symbol-game");
const symbolTarget = document.querySelector("#symbol-target");
const symbolChoices = document.querySelector("#symbol-choices");
const reactionGame = document.querySelector("#reaction-game");
const reactionCue = document.querySelector("#reaction-cue");
const fluencyEntry = document.querySelector("#fluency-entry");
const fluencyInput = document.querySelector("#fluency-input");
const submitActivityButton = document.querySelector("#submit-activity");
const cancelActivityButton = document.querySelector("#cancel-activity");
const reportCard = document.querySelector("#report-card");
const chatTestButton = document.querySelector("#chat-test-button");
const activityCard = document.querySelector(".activity-card");
const activitySection = document.querySelector("#activity-section");
const chatActivityContainer = document.querySelector("#chat-activity-container");
const menuButton = document.querySelector("#menu-button");
const appSidebar = document.querySelector("#app-sidebar");
const darkModeButton = document.querySelector("#dark-mode-button");
const textSizeDecrease = document.querySelector("#text-size-decrease");
const textSizeIncrease = document.querySelector("#text-size-increase");
const textSizeValue = document.querySelector("#text-size-value");
const savedTheme = localStorage.getItem("cogni-theme");
if (savedTheme === "dark") document.body.classList.add("dark-mode");
const textScales = [0.9, 1, 1.1];
let textScaleIndex = Math.max(0, textScales.indexOf(Number(localStorage.getItem("cogni-text-scale"))));
if (!textScales.includes(Number(localStorage.getItem("cogni-text-scale")))) textScaleIndex = 1;

const textSizeLabels = {
  en: { group: "Text size", decrease: "Decrease text size", increase: "Increase text size" },
  hi: { group: "पाठ का आकार", decrease: "पाठ छोटा करें", increase: "पाठ बड़ा करें" },
  mr: { group: "मजकूराचा आकार", decrease: "मजकूर लहान करा", increase: "मजकूर मोठा करा" },
};

function applyTextScale() {
  const scale = textScales[textScaleIndex];
  appShell.style.zoom = String(scale);
  authScreen.style.zoom = String(scale);
  textSizeValue.textContent = `${Math.round(scale * 100)}%`;
  textSizeDecrease.disabled = textScaleIndex === 0;
  textSizeIncrease.disabled = textScaleIndex === textScales.length - 1;
  localStorage.setItem("cogni-text-scale", String(scale));
}

function updateTextSizeLabels() {
  const labels = textSizeLabels[currentLanguage];
  const controls = document.querySelector(".text-size-controls");
  controls.setAttribute("aria-label", labels.group);
  textSizeDecrease.setAttribute("aria-label", labels.decrease);
  textSizeIncrease.setAttribute("aria-label", labels.increase);
}

const activityWords = {
  en: ["mango", "key", "river", "garden", "window", "candle", "basket", "bridge", "lemon", "pencil", "cloud", "button"],
  hi: ["आम", "चाबी", "नदी", "बगीचा", "खिड़की", "दीपक", "टोकरी", "पुल", "नींबू", "कलम", "बादल", "किताब"],
  mr: ["आंबा", "किल्ली", "नदी", "बाग", "खिडकी", "दिवा", "टोपली", "पूल", "लिंबू", "लेखणी", "ढग", "पुस्तक"],
};

const analysisCopy = {
  en: {
    wordTaskTitle: "Word recall",
    wordTaskCopy: "Remember three changing words.",
    fluencyTaskTitle: "Category fluency",
    fluencyTaskCopy: "Name as many animals as you can in 60 seconds.",
    spatialTaskTitle: "Spatial recall",
    spatialTaskCopy: "Remember three positions on a grid.",
    symbolTaskTitle: "Symbol matching",
    symbolTaskCopy: "Choose matching symbols at a comfortable pace.",
    reactionTaskTitle: "Visual response",
    reactionTaskCopy: "Tap when a cue appears; wait when it does not.",
    selectTask: "Today’s activity is ready. Complete each activity at your own pace.",
    recallPrompt: "Remember these words. They will disappear in five seconds.",
    recallAfter: "Enter the words you remember.",
    fluencyPrompt: "Type as many different animals as you can. Separate words with commas or new lines.",
    fluencyAfter: "Time is up. Save the number of unique entries you wrote.",
    spatialPrompt: "Remember which three squares are highlighted.",
    spatialAfter: "Tap the same three squares, then save your result.",
    symbolPrompt: "Choose the same symbol shown above. Take your time.",
    symbolAfter: "You have completed the symbol activity.",
    reactionPrompt: "Tap when the blue circle appears. Wait when the screen is blank.",
    reactionAfter: "You have completed the response activity.",
    fluencyLabel: "Animal names",
    fluencyPlaceholder: "Example: cat, elephant, horse",
    start: "Begin",
    save: "Save result",
    cancel: "Cancel activity",
    cancelConfirm: "Cancel this activity without saving a result?",
    complete: () => "Activity saved. Nice work.",
    activityNames: {
      word_recall: "Word recall",
      category_fluency: "Category fluency",
      spatial_recall: "Spatial sequence",
      symbol_match: "Symbol matching",
      reaction_tap: "Visual response",
    },
    taskSummary: (name) => `${name}: recent entries recorded`,
    trend: () => "Your recent pattern is being tracked against your own usual routine.",
    notEnough: "More entries are needed before a personal pattern can be described.",
    variability: () => "Your entries show some natural day-to-day variation.",
    averageVariability: () => "Your entries show some natural day-to-day variation.",
    noRepeatedScores: "More routine entries are needed before variation can be described.",
    activitySummary: () => "Your recent activity is recorded here.",
    period: () => "Your recent routine",
    reportMetrics: () => "Your recent check-in activity is summarized below.",
    baselineReady: () => "Your personal reference is ready. This is descriptive wellbeing tracking, not a medical alert.",
    baselineBuilding: () => "Your personal reference is still being built. Keep checking in when it feels comfortable.",
    baselineInsufficient: () => "There is not yet enough routine information for a personal reference. No medical alert is produced.",
    reportPrint: "Print / save PDF",
    reportDownload: "Download report PDF",
    noCheckins: "No check-ins recorded",
    noActivities: "No activities recorded",
    analysisTitles: ["Participation", "Activities", "Routine variation"],
    analysisDescriptions: [
      "Counts days with a check-in and activities completed. This is engagement data, not a symptom measure.",
      "Shows which activities you have tried as part of your routine.",
      "Shows that day-to-day variation is normal and is not a diagnosis.",
    ],
    noData: "No saved observations in this period.",
    reportDisclaimer: "Descriptive wellbeing tracking only; this is not medical advice or a diagnosis.",
  },
  hi: {
    wordTaskTitle: "शब्द याद करना",
    wordTaskCopy: "तीन नए शब्द याद रखें।",
    fluencyTaskTitle: "श्रेणी में शब्द बताना",
    fluencyTaskCopy: "60 सेकंड में अधिक से अधिक जानवरों के नाम लिखें।",
    spatialTaskTitle: "स्थान याद करना",
    spatialTaskCopy: "ग्रिड में तीन जगहें याद रखें।",
    symbolTaskTitle: "चिन्ह मिलाना",
    symbolTaskCopy: "आराम से मेल खाते चिन्ह चुनें।",
    reactionTaskTitle: "दृश्य प्रतिक्रिया",
    reactionTaskCopy: "संकेत दिखे तो टैप करें; न दिखे तो प्रतीक्षा करें।",
    selectTask: "आज की गतिविधि तैयार है। इसे अपनी गति से पूरा करें।",
    recallPrompt: "इन शब्दों को याद रखें। ये पाँच सेकंड में छिप जाएँगे।",
    recallAfter: "जो शब्द याद हों, वे लिखें।",
    fluencyPrompt: "जितने अलग-अलग जानवरों के नाम लिख सकें, लिखें। शब्दों के बीच कॉमा या नई पंक्ति रखें।",
    fluencyAfter: "समय पूरा हुआ। लिखे गए अलग-अलग शब्दों की संख्या सहेजें।",
    spatialPrompt: "याद रखें कि कौन-से तीन खाने हाइलाइट हुए हैं।",
    spatialAfter: "वही तीन खाने चुनें, फिर नतीजा सहेजें।",
    symbolPrompt: "ऊपर दिखाए गए जैसा चिन्ह चुनें। आराम से करें।",
    symbolAfter: "चिन्हों वाली गतिविधि पूरी हुई।",
    reactionPrompt: "नीला गोला दिखे तो टैप करें। स्क्रीन खाली हो तो प्रतीक्षा करें।",
    reactionAfter: "प्रतिक्रिया वाली गतिविधि पूरी हुई।",
    fluencyLabel: "जानवरों के नाम",
    fluencyPlaceholder: "उदाहरण: बिल्ली, हाथी, घोड़ा",
    start: "शुरू करें",
    save: "नतीजा सहेजें",
    cancel: "गतिविधि रद्द करें",
    cancelConfirm: "बिना नतीजा सहेजे गतिविधि रद्द करें?",
    complete: () => "गतिविधि सहेजी गई। बहुत अच्छा।",
    activityNames: {
      word_recall: "शब्द याद करना",
      category_fluency: "श्रेणी में शब्द",
      spatial_recall: "स्थान याद करना",
      symbol_match: "चिन्ह मिलाना",
      reaction_tap: "दृश्य प्रतिक्रिया",
    },
    taskSummary: (name, count, average) => `${name}: ${count} गतिविधियाँ · औसत ${average}%`,
    trend: (change) => `शुरुआती और बाद की प्रविष्टियों में ${change > 0 ? "+" : ""}${change} प्रतिशत-अंक का अंतर`,
    notEnough: "शुरुआती और बाद के नतीजों की तुलना के लिए और प्रविष्टियाँ चाहिए।",
    variability: (value) => `दर्ज नतीजों में बदलाव: ${value} प्रतिशत-अंक`,
    averageVariability: (value) => `प्रति गतिविधि औसत बदलाव: ${value} प्रतिशत-अंक`,
    noRepeatedScores: "बदलाव का सारांश दिखाने के लिए बार-बार किए गए नतीजे चाहिए।",
    activitySummary: (count, days) => `${count} गतिविधियाँ · ${days} दिन`,
    period: (start, end) => `पिछले 30 दिन · ${start} से ${end} तक`,
    reportMetrics: (days, messages, responses, attempts, streak, valid) =>
      `${days} बातचीत वाले दिन · ${messages} संदेश · ${responses} जवाब · ${attempts} गतिविधियाँ · ${streak} दिन की लय · ${valid} पूरे दिन`,
    baselineReady: (count) => `व्यक्तिगत संदर्भ अवधि तैयार: ${count} पूरे दिन। यह केवल विवरणात्मक रिकॉर्ड है; कोई चिकित्सकीय चेतावनी नहीं दी जाती।`,
    baselineBuilding: (count) => `व्यक्तिगत संदर्भ बन रहा है: दिन 3–14 में ${count}/10 पूरे दिन। पहले दो दिन परिचय के लिए हैं।`,
    baselineInsufficient: (count) => `संदर्भ अवधि में ${count}/10 आवश्यक पूरे दिन मिले। कोई चिकित्सकीय चेतावनी नहीं दी जाती।`,
    reportPrint: "प्रिंट / PDF सहेजें",
    reportDownload: "रिपोर्ट PDF डाउनलोड करें",
    noCheckins: "इस अवधि में बातचीत दर्ज नहीं हुई",
    noActivities: "इस अवधि में गतिविधि दर्ज नहीं हुई",
    analysisTitles: ["भागीदारी", "गतिविधि नतीजे", "नतीजों में बदलाव"],
    analysisDescriptions: [
      "बातचीत वाले दिन और पूरी की गई गतिविधियाँ गिनता है। यह भागीदारी का रिकॉर्ड है, लक्षण का माप नहीं।",
      "हर गतिविधि का नतीजा उसके अधिकतम अंक के प्रतिशत के रूप में दिखाता है; पर्याप्त प्रविष्टियाँ होने पर शुरुआती और बाद के नतीजों की तुलना होती है।",
      "दोहराए गए नतीजों वाली गतिविधियों में औसत बदलाव दिखाता है। बदलाव अकेले किसी बीमारी या गिरावट का संकेत नहीं है।",
    ],
    noData: "इस अवधि में कोई सहेजा हुआ रिकॉर्ड नहीं।",
    reportDisclaimer: "यह केवल विवरणात्मक रिकॉर्ड है; इसमें AI निदान या चिकित्सकीय सीमा लागू नहीं होती। इसे जाँच नतीजे के बजाय डॉक्टर से बातचीत के संदर्भ के रूप में साझा करें।",
  },
  mr: {
    wordTaskTitle: "शब्द आठवणे",
    wordTaskCopy: "तीन वेगवेगळे शब्द लक्षात ठेवा.",
    fluencyTaskTitle: "गटातील शब्द",
    fluencyTaskCopy: "60 सेकंदांत शक्य तितक्या प्राण्यांची नावे लिहा.",
    spatialTaskTitle: "जागा आठवणे",
    spatialTaskCopy: "जाळीतील तीन जागा लक्षात ठेवा.",
    symbolTaskTitle: "चिन्ह जुळवणे",
    symbolTaskCopy: "सोयीच्या गतीने जुळणारी चिन्हे निवडा.",
    reactionTaskTitle: "दृश्य प्रतिसाद",
    reactionTaskCopy: "संकेत दिसल्यावर टॅप करा; नसेल तर थांबा.",
    selectTask: "आजचा उपक्रम तयार आहे. तो तुमच्या गतीने पूर्ण करा.",
    recallPrompt: "हे शब्द लक्षात ठेवा. पाच सेकंदांत ते दिसेनासे होतील.",
    recallAfter: "आठवणारे शब्द लिहा.",
    fluencyPrompt: "शक्य तितक्या वेगवेगळ्या प्राण्यांची नावे लिहा. शब्द स्वल्पविरामाने किंवा नवीन ओळीने वेगळे करा.",
    fluencyAfter: "वेळ संपला. लिहिलेल्या वेगवेगळ्या शब्दांची संख्या जतन करा.",
    spatialPrompt: "हायलाइट केलेले तीन चौकोन लक्षात ठेवा.",
    spatialAfter: "तेच तीन चौकोन निवडा आणि निकाल जतन करा.",
    symbolPrompt: "वर दाखवलेले तेच चिन्ह निवडा. घाई करू नका.",
    symbolAfter: "चिन्हांचा उपक्रम पूर्ण झाला.",
    reactionPrompt: "निळे वर्तुळ दिसल्यावर टॅप करा. स्क्रीन रिकामी असल्यास थांबा.",
    reactionAfter: "प्रतिसादाचा उपक्रम पूर्ण झाला.",
    fluencyLabel: "प्राण्यांची नावे",
    fluencyPlaceholder: "उदा.: मांजर, हत्ती, घोडा",
    start: "सुरू करा",
    save: "निकाल जतन करा",
    cancel: "उपक्रम रद्द करा",
    cancelConfirm: "निकाल न जतन करता उपक्रम रद्द करायचा?",
    complete: () => "उपक्रम जतन झाला. छान केले.",
    activityNames: {
      word_recall: "शब्द आठवणे",
      category_fluency: "गटातील शब्द",
      spatial_recall: "जागा आठवणे",
      symbol_match: "चिन्ह जुळवणे",
      reaction_tap: "दृश्य प्रतिसाद",
    },
    taskSummary: (name, count, average) => `${name}: ${count} उपक्रम · सरासरी ${average}%`,
    trend: (change) => `सुरुवातीच्या आणि नंतरच्या नोंदींमध्ये ${change > 0 ? "+" : ""}${change} टक्के-अंकांचा फरक`,
    notEnough: "सुरुवातीच्या आणि नंतरच्या निकालांची तुलना करण्यासाठी आणखी नोंदी हव्यात.",
    variability: (value) => `नोंदवलेल्या निकालांतील बदल: ${value} टक्के-अंक`,
    averageVariability: (value) => `प्रति उपक्रम सरासरी बदल: ${value} टक्के-अंक`,
    noRepeatedScores: "बदलाचा सारांश दाखवण्यासाठी पुन्हा केलेले निकाल आवश्यक आहेत.",
    activitySummary: (count, days) => `${count} उपक्रम · ${days} दिवस`,
    period: (start, end) => `मागील 30 दिवस · ${start} ते ${end}`,
    reportMetrics: (days, messages, responses, attempts, streak, valid) =>
      `${days} विचारपुशीचे दिवस · ${messages} संदेश · ${responses} उत्तरे · ${attempts} उपक्रम · ${streak} दिवसांची सलग नोंद · ${valid} पूर्ण दिवस`,
    baselineReady: (count) => `वैयक्तिक संदर्भ कालावधी तयार: ${count} पूर्ण दिवस. हा फक्त वर्णनात्मक मागोवा आहे; वैद्यकीय सूचना दिली जात नाही.`,
    baselineBuilding: (count) => `वैयक्तिक संदर्भ तयार होत आहे: दिवस 3–14 मधील ${count}/10 पूर्ण दिवस. पहिले दोन दिवस सरावासाठी आहेत.`,
    baselineInsufficient: (count) => `संदर्भ कालावधीत आवश्यक 10 पैकी ${count} पूर्ण दिवस नोंदले. वैद्यकीय सूचना दिली जात नाही.`,
    reportPrint: "प्रिंट / PDF जतन करा",
    reportDownload: "अहवाल PDF डाउनलोड करा",
    noCheckins: "या काळात विचारपूस नोंदलेली नाही",
    noActivities: "या काळात उपक्रम नोंदलेला नाही",
    analysisTitles: ["सहभाग", "उपक्रम निकाल", "निकालांतील बदल"],
    analysisDescriptions: [
      "विचारपुशीचे दिवस आणि पूर्ण केलेले उपक्रम मोजतो. ही सहभागाची नोंद आहे, लक्षणांचे मोजमाप नाही.",
      "प्रत्येक उपक्रमाचा निकाल कमाल गुणांच्या टक्केवारीत दाखवतो; पुरेशा नोंदी असल्यास सुरुवातीच्या व नंतरच्या निकालांची तुलना करतो.",
      "पुन्हा केलेल्या उपक्रमांतील सरासरी बदल दाखवतो. बदल एकट्याने आजार किंवा घसरण दर्शवत नाही.",
    ],
    noData: "या काळात जतन केलेली नोंद नाही.",
    reportDisclaimer: "हा फक्त वर्णनात्मक मागोवा आहे; AI निदान किंवा वैद्यकीय मर्यादा लागू नाही. चाचणी निकालाऐवजी डॉक्टरांशी चर्चेसाठी संदर्भ म्हणून शेअर करा.",
  },
};

const translations = {
  en: {
    introEyebrow: "DAILY WELLBEING",
    introTitle: "A calmer way to check in.",
    introCopy: "A familiar place to share how your day is going and try a short memory activity.",
    eyebrow: "COGNI CHECKIN",
    title: "Cogni Checkin",
    assistantName: "Cogni Checkin",
    opening: "How are you feeling today? Or, if you prefer, we can just chat about anything on your mind.",
    wellTitle: "How are you feeling?",
    wellSubtitle: "A simple check-in",
    wellMessage: "I'm doing okay today.",
    talkTitle: "Let's just talk",
    talkSubtitle: "Anything you like",
    talkMessage: "I'd like to talk about something on my mind.",
    inputLabel: "Write a message",
    inputPlaceholder: "Write a message...",
    send: "Send",
    consent: "I agree to save my check-ins and activity results in this app. I can delete them below.",
    privacy: "Saved in the app database · Avoid names or sensitive details",
    clearConversation: "Delete saved data",
    clearConfirm: "Delete saved check-ins and activity results? This cannot be undone.",
    clearSuccess: "Your saved data was deleted.",
    clearError: "Saved data could not be deleted. Please try again.",
    activityEyebrow: "TODAY’S ACTIVITY",
    activityTitle: "Daily activities",
    activityDescription: "Complete today’s short activity as part of your routine.",
    activityDuration: "1–2 minutes",
    secondsLeft: (seconds) => `${seconds} seconds`,
    recallPlaceholder: (number) => `Word ${number}`,
    activityError: "The result could not be saved. Please try again.",
    activityConsent: "Please agree to save activity results before starting.",
    activityDisclaimer: "These activities are not clinically validated cognitive tests. Scores cannot diagnose or rule out a condition.",
    reportEyebrow: "30-DAY SUMMARY",
    reportTitle: "Your activity report",
    reportDescription: "A factual summary of check-ins and completed activities.",
    refreshReport: "Refresh",
    reportError: "Activity history could not be loaded.",
    loadingReport: "Loading your activity history…",
    safety: "Cogni-Routine provides wellbeing tracking and a mild cognitive activity. It is not medical advice or a diagnosis. Talk with a qualified healthcare professional about concerns.",
    greeting: ["Good morning", "Good afternoon", "Good evening"],
    consentRequired: "Please read and accept the data notice before sending a message.",
    loadError: "Could not load this conversation. Check that the app server is running, then refresh.",
    sendError: "Your message was not sent. Check your connection and try again.",
    retry: "Try again",
  },
  hi: {
    introEyebrow: "रोज़मर्रा का स्वास्थ्य",
    introTitle: "बातचीत का एक शांत तरीका।",
    introCopy: "दिन कैसा बीत रहा है, यह साझा करने और छोटा स्मृति अभ्यास करने की परिचित जगह।",
    eyebrow: "रोज़ की बातचीत",
    title: "Cogni Checkin",
    assistantName: "Cogni Checkin",
    opening: "आज आप कैसा महसूस कर रहे हैं? चाहें तो हम आपकी पसंद की किसी भी बात पर बातचीत कर सकते हैं।",
    wellTitle: "आज कैसा महसूस हो रहा है?",
    wellSubtitle: "एक छोटी-सी बातचीत",
    wellMessage: "आज मैं ठीक हूँ।",
    talkTitle: "कुछ बात करें",
    talkSubtitle: "जो चाहें, उस बारे में",
    talkMessage: "मैं अपने मन की एक बात साझा करना चाहता हूँ।",
    inputLabel: "अपना संदेश लिखें",
    inputPlaceholder: "अपना संदेश लिखें...",
    send: "भेजें",
    consent: "मैं अपनी बातचीत और गतिविधि के नतीजे इस ऐप में सहेजने की सहमति देता/देती हूँ। मैं उन्हें नीचे से हटा सकता/सकती हूँ।",
    privacy: "ऐप डेटाबेस में सहेजा जाता है · नाम या संवेदनशील जानकारी न लिखें",
    clearConversation: "सहेजा डेटा हटाएँ",
    clearConfirm: "सहेजी गई बातचीत और गतिविधि नतीजे हटाएँ? इसे वापस नहीं किया जा सकता।",
    clearSuccess: "आपका सहेजा हुआ डेटा हटा दिया गया है।",
    clearError: "सहेजा डेटा हटाया नहीं जा सका। कृपया फिर कोशिश करें।",
    activityEyebrow: "आज की गतिविधि",
    activityTitle: "दैनिक गतिविधियाँ",
    activityDescription: "अपनी दिनचर्या के हिस्से के रूप में आज की छोटी गतिविधि पूरी करें।",
    activityDuration: "1–2 मिनट",
    secondsLeft: (seconds) => `${seconds} सेकंड`,
    recallPlaceholder: (number) => `शब्द ${number}`,
    activityError: "नतीजा सहेजा नहीं जा सका। कृपया फिर कोशिश करें।",
    activityConsent: "गतिविधि शुरू करने से पहले नतीजे सहेजने की सहमति दें।",
    activityDisclaimer: "ये गतिविधियाँ चिकित्सकीय रूप से सत्यापित संज्ञानात्मक जाँच नहीं हैं। इनके अंक किसी स्थिति का निदान या खंडन नहीं कर सकते।",
    reportEyebrow: "30-दिन का सारांश",
    reportTitle: "आपकी गतिविधि रिपोर्ट",
    reportDescription: "बातचीत और पूरी की गई गतिविधियों का तथ्यात्मक सारांश।",
    refreshReport: "ताज़ा करें",
    reportError: "गतिविधि का इतिहास लोड नहीं हो सका।",
    loadingReport: "आपकी गतिविधि का इतिहास लोड हो रहा है…",
    safety: "Cogni-Routine रोज़मर्रा के स्वास्थ्य में मदद के लिए है। यह चिकित्सा जाँच या निदान नहीं है और यह नहीं बता सकता कि किसी को डिमेंशिया, MCI, डिलीरियम, अवसाद, पार्किंसन रोग या अन्य स्थिति है या नहीं। चिंता होने पर योग्य स्वास्थ्यकर्मी से बात करें।",
    greeting: ["सुप्रभात", "नमस्कार", "शुभ संध्या"],
    consentRequired: "संदेश भेजने से पहले कृपया डेटा सूचना पढ़कर सहमति दें।",
    loadError: "यह बातचीत लोड नहीं हो सकी। सर्वर चालू है या नहीं जाँचें और पेज फिर से खोलें।",
    sendError: "संदेश नहीं भेजा गया। कनेक्शन जाँचकर फिर कोशिश करें।",
    retry: "फिर कोशिश करें",
  },
  mr: {
    introEyebrow: "रोजचे आरोग्य",
    introTitle: "मनमोकळ्या संवादाची जागा.",
    introCopy: "दिवस कसा जातोय हे सांगण्यासाठी आणि छोटा स्मरण-उपक्रम करण्यासाठी परिचित जागा.",
    eyebrow: "रोजची विचारपूस",
    title: "Cogni Checkin",
    assistantName: "Cogni Checkin",
    opening: "आज तुम्हाला कसे वाटत आहे? किंवा तुम्हाला आवडेल त्या कोणत्याही विषयावर आपण बोलू शकतो.",
    wellTitle: "आज कसे वाटत आहे?",
    wellSubtitle: "एक छोटीशी विचारपूस",
    wellMessage: "आज मला ठीक वाटत आहे.",
    talkTitle: "गप्पा मारूया",
    talkSubtitle: "तुमच्या आवडीच्या विषयावर",
    talkMessage: "माझ्या मनातली एक गोष्ट सांगायची आहे.",
    inputLabel: "संदेश लिहा",
    inputPlaceholder: "संदेश लिहा...",
    send: "पाठवा",
    consent: "माझी विचारपूस आणि उपक्रमांचे निकाल या अॅपमध्ये जतन करण्यास मी संमती देतो/देते. खालील पर्यायाने ते हटवता येतील.",
    privacy: "अॅप डेटाबेसमध्ये जतन होते · कृपया नावे किंवा संवेदनशील माहिती लिहू नका",
    clearConversation: "जतन केलेला डेटा हटवा",
    clearConfirm: "जतन केलेली विचारपूस आणि उपक्रमांचे निकाल हटवायचे? ही कृती पूर्ववत करता येणार नाही.",
    clearSuccess: "तुमचा जतन केलेला डेटा हटवला आहे.",
    clearError: "जतन केलेला डेटा हटवता आला नाही. कृपया पुन्हा प्रयत्न करा.",
    activityEyebrow: "आजचा उपक्रम",
    activityTitle: "दैनिक उपक्रम",
    activityDescription: "तुमच्या दिनक्रमाचा भाग म्हणून आजचा छोटा उपक्रम पूर्ण करा.",
    activityDuration: "1–2 मिनिटे",
    secondsLeft: (seconds) => `${seconds} सेकंद`,
    recallPlaceholder: (number) => `शब्द ${number}`,
    activityError: "निकाल जतन करता आला नाही. कृपया पुन्हा प्रयत्न करा.",
    activityConsent: "उपक्रम सुरू करण्यापूर्वी निकाल जतन करण्यास संमती द्या.",
    activityDisclaimer: "हे उपक्रम वैद्यकीयदृष्ट्या प्रमाणित संज्ञानात्मक चाचण्या नाहीत. गुणांवरून कोणत्याही स्थितीचे निदान किंवा नकार देता येत नाही.",
    reportEyebrow: "30 दिवसांचा सारांश",
    reportTitle: "तुमचा उपक्रम अहवाल",
    reportDescription: "विचारपूस आणि पूर्ण केलेल्या उपक्रमांचा तथ्यात्मक सारांश.",
    refreshReport: "रीफ्रेश करा",
    reportError: "उपक्रमांचा इतिहास लोड करता आला नाही.",
    loadingReport: "तुमचा उपक्रमांचा इतिहास लोड होत आहे…",
    safety: "Cogni-Routine रोजच्या आरोग्यासाठी मदत करते. ही वैद्यकीय चाचणी किंवा निदान नाही; डिमेन्शिया, MCI, डिलिरियम, नैराश्य, पार्किन्सन रोग किंवा इतर आजार आहेत का हे ती सांगू शकत नाही. काळजी वाटल्यास पात्र आरोग्यतज्ज्ञांशी बोला.",
    greeting: ["शुभ सकाळ", "शुभ दुपार", "शुभ संध्याकाळ"],
    consentRequired: "संदेश पाठवण्यापूर्वी कृपया डेटा सूचना वाचून संमती द्या.",
    loadError: "ही नोंद लोड करता आली नाही. सर्व्हर सुरू आहे का ते तपासून पेज पुन्हा उघडा.",
    sendError: "संदेश पाठवला गेला नाही. कनेक्शन तपासून पुन्हा प्रयत्न करा.",
    retry: "पुन्हा प्रयत्न करा",
  },
};

const supportedLanguages = Object.keys(translations);
let currentLanguage = localStorage.getItem("cogni-language");
if (!supportedLanguages.includes(currentLanguage)) currentLanguage = "en";
languageSelect.value = currentLanguage;

let hasMessages = false;
let hasActivityRecords = false;
let activityStartedAt = 0;
let activeWords = [];
let activeTask = null;
let voiceRecognition = null;
let voiceListening = false;
let activeTargets = [];
let selectedTargets = new Set();
let activityTimerId = null;
let symbolRounds = [];
let symbolRoundIndex = 0;
let symbolCorrect = 0;
let symbolResponseTimes = [];
let symbolRoundStartedAt = 0;
let reactionPlan = [];
let reactionIndex = 0;
let reactionCorrect = 0;
let reactionFalseTaps = 0;
let reactionMisses = 0;
let reactionTimes = [];
let reactionState = "waiting";
let reactionTimeoutIds = [];
let participantId = null;
let currentAccount = null;
let questionShownAt = performance.now();
let typedCorrections = 0;
let lastSentText = "";
let typingStartedAt = null;
let keypressCount = 0;
let voiceStartedAt = null;
let voiceDurationMs = null;
let dailySession = null;
let voiceTranscript = "";

const voicePracticeWords = {
  en: ["river", "garden", "window", "candle", "morning", "silver"],
  hi: ["नदी", "बगीचा", "खिड़की", "दीपक", "सुबह", "चाँदी"],
  mr: ["नदी", "बाग", "खिडकी", "दिवा", "सकाळ", "चांदी"],
};

function currentLocale() {
  return { en: "en-IN", hi: "hi-IN", mr: "mr-IN" }[currentLanguage];
}

function voicePracticeWord() {
  if (dailySession?.voice_practice_word) return dailySession.voice_practice_word;
  const words = voicePracticeWords[currentLanguage];
  return words[dailySeed() % words.length];
}

function voiceMatchesPracticeWord(transcript) {
  return normalizeAnswer(transcript)
    .split(/\s+/u)
    .includes(normalizeAnswer(voicePracticeWord()));
}

function formatGreeting() {
  const hour = new Date().getHours();
  const partOfDay = hour < 12 ? 0 : hour < 17 ? 1 : 2;
  return `${translations[currentLanguage].greeting[partOfDay]}.`;
}

function renderLanguage() {
  const copy = translations[currentLanguage];
  updateTextSizeLabels();
  document.documentElement.lang = currentLanguage;
  document.querySelector("#eyebrow").textContent = copy.eyebrow;
  document.querySelector("#chat-title").textContent = currentAccount?.name
    ? `Welcome, ${currentAccount.name}`
    : copy.title;
  document.querySelector("#assistant-name").textContent = copy.assistantName;
  document.querySelector("#opening-question").textContent = copy.opening;
  document.querySelector("#input-label").textContent = copy.inputLabel;
  messageInput.placeholder = copy.inputPlaceholder;
  sendButton.setAttribute("aria-label", copy.send);
  sendButton.querySelector("span").textContent = copy.send;
  document.querySelector("#consent-copy").textContent = copy.consent;
  document.querySelector("#privacy-note").textContent = copy.privacy;
  clearButton.textContent = copy.clearConversation;
  clearButton.disabled = !(hasMessages || hasActivityRecords);
  document.querySelector("#safety-copy").textContent = copy.safety;
  document.querySelector("#activity-eyebrow").textContent = copy.activityEyebrow;
  document.querySelector("#activity-title").textContent = copy.activityTitle;
  document.querySelector("#activity-description").textContent = copy.activityDescription;
  document.querySelector("#activity-duration").textContent = copy.activityDuration;
  const activityCopy = analysisCopy[currentLanguage];
  document.querySelector("#activity-selection-copy").textContent = activityCopy.selectTask;
  document.querySelector("#word-task-title").textContent = activityCopy.wordTaskTitle;
  document.querySelector("#word-task-copy").textContent = activityCopy.wordTaskCopy;
  document.querySelector("#fluency-task-title").textContent = activityCopy.fluencyTaskTitle;
  document.querySelector("#fluency-task-copy").textContent = activityCopy.fluencyTaskCopy;
  document.querySelector("#spatial-task-title").textContent = activityCopy.spatialTaskTitle;
  document.querySelector("#spatial-task-copy").textContent = activityCopy.spatialTaskCopy;
  document.querySelector("#symbol-task-title").textContent = activityCopy.symbolTaskTitle;
  document.querySelector("#symbol-task-copy").textContent = activityCopy.symbolTaskCopy;
  document.querySelector("#reaction-task-title").textContent = activityCopy.reactionTaskTitle;
  document.querySelector("#reaction-task-copy").textContent = activityCopy.reactionTaskCopy;
  document.querySelector("#activity-disclaimer").textContent = copy.activityDisclaimer;
  document.querySelector("#report-eyebrow").textContent = copy.reportEyebrow;
  document.querySelector("#report-title").textContent = copy.reportTitle;
  document.querySelector("#report-description").textContent = copy.reportDescription;
  document.querySelector("#refresh-report").textContent = copy.refreshReport;
  document.querySelector("#download-report").textContent = activityCopy.reportDownload;
  document.querySelector("#print-report").textContent = activityCopy.reportPrint;
  for (const [index, input] of [...recallForm.querySelectorAll("input")].entries()) {
    input.placeholder = copy.recallPlaceholder(index + 1);
    input.parentElement.querySelector(".sr-only").textContent = copy.recallPlaceholder(index + 1);
  }
  document.querySelector("#fluency-label").textContent = activityCopy.fluencyLabel;
  fluencyInput.placeholder = activityCopy.fluencyPlaceholder;
  submitActivityButton.textContent = activityCopy.save;
  cancelActivityButton.textContent = activityCopy.cancel;

  const now = new Date();
  greetingElement.textContent = formatGreeting();
  greetingTimeElement.textContent = now.toLocaleTimeString(currentLocale(), {
    hour: "numeric",
    minute: "2-digit",
  });
  dateElement.textContent = now.toLocaleDateString(currentLocale(), {
    weekday: "long",
    month: "long",
    day: "numeric",
  });

  sendButton.disabled = !consentCheckbox.checked;
}

function setAuthMode(mode) {
  const isRegistering = mode === "register";
  registerForm.hidden = !isRegistering;
  loginForm.hidden = isRegistering;
  document.querySelector("#show-register").setAttribute("aria-selected", String(isRegistering));
  document.querySelector("#show-login").setAttribute("aria-selected", String(!isRegistering));
  authStatus.textContent = "";
}

function showAuthError(error, fallback) {
  authStatus.textContent = error?.message || fallback;
  authStatus.classList.add("error");
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: {
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...options.headers,
    },
  });
  const payload = response.status === 204 ? null : await response.json();
  if (!response.ok) throw new Error(payload?.detail || `Request failed (${response.status}).`);
  return payload;
}

function updateProfileForm(profile) {
  for (const [key, value] of Object.entries(profile)) {
    const input = profileForm.elements.namedItem(key);
    if (input) input.value = value ?? "";
  }
  document.querySelector("#sidebar-user").textContent = profile.name;
  languageSelect.value = profile.language;
  currentLanguage = profile.language;
}

async function enterApplication(account) {
  currentAccount = account;
  participantId = account.participant_id;
  authScreen.hidden = true;
  appShell.hidden = false;
  consentCheckbox.checked = true;
  aiConsentCheckbox.checked = account.ai_consented;
  updateProfileForm(account);
  showView("chat-card");
  renderLanguage();
  appShell.setAttribute("aria-busy", "true");
  showStatus("Loading your check-in…");
  const results = await Promise.allSettled([
    loadHistory(),
    loadReport(),
    loadDailyQuestion(),
    loadDailySession(),
  ]);
  appShell.removeAttribute("aria-busy");
  showStatus("");
  if (results.some((result) => result.status === "rejected")) {
    showStatus("Some check-in data could not be loaded.", true);
    addRetryButton(statusMessage, () => enterApplication(currentAccount));
  }
  updateActivityVisibility();
}

function addRetryButton(container, retry) {
  container.querySelector(".retry-button")?.remove();
  const button = document.createElement("button");
  button.className = "retry-button";
  button.type = "button";
  button.textContent = translations[currentLanguage].retry;
  button.addEventListener("click", retry, { once: true });
  container.append(" ", button);
}

async function loadDailySession() {
  dailySession = await requestJson("/api/sessions/today", { method: "POST" });
  updateActivityVisibility();
}

function updateActivityVisibility() {
  const chatIsVisible = !document.querySelector("#chat-card")?.hidden;
  const showInChat = hasMessages && chatIsVisible && !activeTask;
  const showInActivityView = !chatIsVisible;
  activityOptions.hidden = !(showInChat || showInActivityView);
  const currentStep = dailySession?.session?.next;
  const activityReady = currentStep?.type === "game";
  chatTestButton.hidden = !(showInChat && activityReady);
  const buttons = [...activityOptions.querySelectorAll("[data-task]")];
  if (buttons.length && participantId) {
    const ordered = dailyShuffle(buttons);
    ordered.forEach((button) => activityOptions.append(button));
    const currentGame = activityReady ? currentStep.game_id : null;
    for (const button of buttons) {
      const buttonGame = button.dataset.task === "spatial_recall"
        ? "pattern_recall"
        : button.dataset.task;
      button.disabled = !activityReady || buttonGame !== currentGame;
    }
  }
}

function showView(viewId) {
  const viewIds = ["chat-card", "activity-section", "report-section", "profile-section", "track-section", "about-section"];
  if (viewId === "chat-card" && activityCard.parentElement !== chatActivityContainer) {
    chatActivityContainer.append(activityCard);
  } else if (viewId === "activity-section" && activityCard.parentElement !== activitySection) {
    activitySection.querySelector(".section-heading").after(activityCard);
  }
  for (const id of viewIds) {
    const section = document.querySelector(`#${id}`);
    if (section) section.hidden = id !== viewId;
  }
  for (const link of document.querySelectorAll("[data-view]")) {
    link.toggleAttribute("aria-current", link.dataset.view === viewId);
  }
  updateActivityVisibility();
  appShell.classList.remove("sidebar-open");
  menuButton?.setAttribute("aria-expanded", "false");
  if (viewId === "report-section") {
    loadReport().catch((error) => {
      reportCard.setAttribute("aria-busy", "false");
      reportCard.textContent = translations[currentLanguage].reportError;
      addRetryButton(reportCard, () => loadReport().catch((retryError) => {
        reportCard.setAttribute("aria-busy", "false");
        reportCard.textContent = translations[currentLanguage].reportError;
        addRetryButton(reportCard, () => showView("report-section"));
        console.error("Unable to retry activity report:", retryError);
      }));
      console.error("Unable to load activity report:", error);
    });
  }
  if (viewId === "track-section" || viewId === "about-section") {
    loadReport().catch((error) => {
      const target = viewId === "track-section"
        ? document.querySelector("#track-card")
        : document.querySelector("#about-report-grid");
      target.textContent = translations[currentLanguage].reportError;
      addRetryButton(target, () => showView(viewId));
      console.error(`Unable to load ${viewId} data:`, error);
    });
  }

}

function activityDifficulty() {
  return dailySeed() % 4;
}

function activityWordCount() {
  return 3 + activityDifficulty();
}

function sessionEventId() {
  if (window.crypto?.randomUUID) return window.crypto.randomUUID();
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function dailySeed() {
  const today = new Date().toLocaleDateString("en-CA");
  const input = `${participantId || "guest"}:${today}`;
  let hash = 2166136261;
  for (const character of input) {
    hash ^= character.charCodeAt(0);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

function dailyShuffle(items) {
  const result = [...items];
  let seed = dailySeed();
  for (let index = result.length - 1; index > 0; index -= 1) {
    seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
    const swapIndex = seed % (index + 1);
    [result[index], result[swapIndex]] = [result[swapIndex], result[index]];
  }
  return result;
}

async function loadDailyQuestion() {
  const response = await fetch(`/api/daily-question/${participantId}?language=${currentLanguage}`);
  if (!response.ok) throw new Error(`Daily question request failed (${response.status}).`);
  const question = await response.json();
  document.querySelector("#opening-question").textContent = question.text;
  questionShownAt = performance.now();
}

async function initializeTelegramApplication() {
  const telegram = window.Telegram?.WebApp;
  if (!telegram?.initData) return false;
  telegram.ready();
  telegram.expand();
  const consented = window.confirm(
    "Allow Cogni-Routine to save your profile, check-ins, and activity results in this app? You can delete them later.",
  );
  if (!consented) {
    showAuthError(new Error("Consent is required before Telegram sign-in."), "Telegram sign-in was cancelled.");
    return true;
  }
  try {
    await requestJson("/api/auth/telegram", {
      method: "POST",
      body: JSON.stringify({
        init_data: telegram.initData,
        consented: true,
        language: languageSelect.value,
        name: telegram.initDataUnsafe?.user?.first_name || "Telegram participant",
      }),
    });
    await enterApplication(await requestJson("/api/auth/me"));
  } catch (error) {
    showAuthError(error, "Telegram sign-in failed. Please try again.");
  }
  return true;
}

async function initializeApplication() {
  renderLanguage();
  if (await initializeTelegramApplication()) return;
  try {
    const account = await requestJson("/api/auth/me");
    await enterApplication(account);
  } catch (error) {
    if (error.message.startsWith("Sign in") || error.message.startsWith("Your session expired")) {
      authScreen.hidden = false;
      appShell.hidden = true;
      return;
    }
    showAuthError(error, "Could not load your account.");
  }
}

async function submitAuthForm(form, endpoint, includeProfile) {
  const payload = Object.fromEntries(new FormData(form).entries());
  if (includeProfile) {
    payload.age = Number(payload.age);
    payload.consented = form.elements.namedItem("consented").checked;
  }
  try {
    authStatus.classList.remove("error");
    authStatus.textContent = "Please wait…";
    const account = await requestJson(endpoint, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    const fullAccount = await requestJson("/api/auth/me");
    await enterApplication(fullAccount);
    authStatus.textContent = "";
    if (includeProfile && aiConsentCheckbox.checked) {
      await requestJson("/api/consent/gemini", {
        method: "PUT",
        body: JSON.stringify({ consented: true }),
      });
      currentAccount.ai_consented = true;
    }
    void account;
  } catch (error) {
    showAuthError(error, "Account access failed. Please try again.");
  }
}

function renderMessage(message) {
  const article = document.createElement("article");
  article.className = message.sender === "user" ? "conversation-message" : "message assistant-followup";

  const content = document.createElement("div");
  content.className = "message-content";
  if (message.sender === "assistant") {
    const senderName = document.createElement("p");
    senderName.className = "message-sender";
    senderName.textContent = translations[currentLanguage].assistantName;
    content.append(senderName);
  }

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  const paragraph = document.createElement("p");
  paragraph.textContent = message.text;
  bubble.append(paragraph);
  content.append(bubble);

  const time = document.createElement("time");
  time.className = "message-time";
  time.dateTime = message.created_at;
  time.textContent = new Date(message.created_at).toLocaleTimeString(currentLocale(), {
    hour: "numeric",
    minute: "2-digit",
  });
  content.append(time);

  article.append(content);
  chatLog.append(article);
  article.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function showStatus(message, isError = false) {
  statusMessage.textContent = message;
  statusMessage.classList.toggle("error", isError);
}

async function loadHistory() {
  const response = await fetch(`/api/conversations/${participantId}`);
  if (!response.ok) throw new Error(`History request failed (${response.status}).`);

  const history = await response.json();
  chatLog.querySelectorAll(".conversation-message, .assistant-followup").forEach((node) => node.remove());
  hasMessages = history.messages.length > 0;
  updateActivityVisibility();
  for (const message of history.messages) renderMessage(message);
  renderLanguage();
}

async function loadReport() {
  reportCard.setAttribute("aria-busy", "true");
  reportCard.textContent = translations[currentLanguage].loadingReport;
  let response;
  try {
    response = await fetch(`/api/reports/${participantId}`);
  } catch (error) {
    reportCard.setAttribute("aria-busy", "false");
    throw error;
  }
  if (!response.ok) {
    reportCard.setAttribute("aria-busy", "false");
    throw new Error(`Report request failed (${response.status}).`);
  }

  const report = await response.json();
  const { attempts } = report;
  hasActivityRecords = attempts.length > 0;
  renderLanguage();
  reportCard.replaceChildren();
  const copy = analysisCopy[currentLanguage];
  const summary = document.createElement("p");
  summary.className = "report-period";
  const periodStart = new Date(`${report.period_start}T00:00:00`);
  const periodEnd = new Date(`${report.period_end}T00:00:00`);
  summary.textContent = `${copy.period(
    periodStart.toLocaleDateString(currentLocale(), { month: "short", day: "numeric" }),
    periodEnd.toLocaleDateString(currentLocale(), { month: "short", day: "numeric" }),
  )} · ${copy.reportMetrics(
    report.checkin_days,
    report.user_messages,
    report.assistant_responses,
    attempts.length,
    report.current_streak,
    report.valid_days,
  )}`;
  reportCard.append(summary);
  const baseline = document.createElement("p");
  baseline.className = "baseline-status";
  baseline.textContent = report.baseline_ready
    ? copy.baselineReady(report.baseline_days)
    : report.days_since_signup <= 14
      ? copy.baselineBuilding(report.baseline_days)
      : copy.baselineInsufficient(report.baseline_days);
  reportCard.append(baseline);
  const baselineAnalysis = report.baseline_analysis || {};
  const baselineNote = document.createElement("p");
  baselineNote.className = "baseline-status";
  baselineNote.textContent = baselineAnalysis.persistent_change
    ? "Your recent routine differs from your usual pattern in more than one area. This is not a diagnosis; consider discussing persistent changes with a qualified professional."
    : baselineAnalysis.calibration?.observed_domains
      ? "Your recent activity is being compared with your own early-use pattern. This is descriptive tracking, not a diagnosis."
      : "More repeated activity data is needed to build a personal reference pattern.";
  reportCard.append(baselineNote);
  if (baselineAnalysis.data_quality?.length) {
    const quality = document.createElement("p");
    quality.className = "report-note";
    quality.textContent = `Data quality notes: ${baselineAnalysis.data_quality.join("; ")}.`;
    reportCard.append(quality);
  }

  const analyzers = document.createElement("div");
  analyzers.className = "analysis-grid";
  const activityDays = report.daily.filter((day) => day.task_count > 0).length;
  const grouped = new Map();
  for (const attempt of attempts) {
    const rows = grouped.get(attempt.task_name) ?? [];
    rows.push(attempt);
    grouped.set(attempt.task_name, rows);
  }
  const repeatedVariations = [...grouped.values()]
    .filter((rows) => rows.length > 1)
    .map((rows) => {
      const percentages = rows.map((attempt) => (attempt.score / attempt.max_score) * 100);
      const average = percentages.reduce((sum, score) => sum + score, 0) / percentages.length;
      const variance =
        percentages.reduce((sum, score) => sum + (score - average) ** 2, 0) / percentages.length;
      return Math.sqrt(variance);
    });
  const averageVariation = repeatedVariations.length
    ? repeatedVariations.reduce((sum, variation) => sum + variation, 0) / repeatedVariations.length
    : null;
  const metrics = [
    "Your check-ins are recorded",
    copy.activitySummary(attempts.length, activityDays),
    averageVariation === null
      ? copy.noRepeatedScores
      : copy.averageVariability(averageVariation.toFixed(1)),
  ];
  for (const [index, title] of copy.analysisTitles.entries()) {
    const card = document.createElement("article");
    card.className = "analysis-card";
    const heading = document.createElement("h3");
    heading.textContent = title;
    const value = document.createElement("strong");
    value.textContent = metrics[index];
    const description = document.createElement("p");
    description.textContent = copy.analysisDescriptions[index];
    card.append(heading, value, description);
    analyzers.append(card);
  }
  reportCard.append(analyzers);

  if (report.user_messages === 0 && attempts.length === 0) {
    const empty = document.createElement("p");
    empty.className = "report-empty";
    empty.textContent = copy.noData;
    reportCard.append(empty);
    reportCard.setAttribute("aria-busy", "false");
    renderTrack(report);
    renderAboutReport(report);
    return;
  }

  const taskResults = document.createElement("div");
  taskResults.className = "task-results";
  const taskNames = ["word_recall", "category_fluency", "spatial_recall", "symbol_match", "reaction_tap"];
  for (const taskName of taskNames) {
    const rows = grouped.get(taskName) ?? [];
    if (rows.length === 0) continue;
    const item = document.createElement("article");
    item.className = "task-result";
    const heading = document.createElement("h3");
    heading.textContent = copy.activityNames[taskName];
    const stat = document.createElement("p");
    stat.textContent = copy.taskSummary(copy.activityNames[taskName], rows.length);
    item.append(heading, stat);

    const trend = document.createElement("p");
    trend.className = "trend-summary";
    trend.textContent = copy.trend();
    const variation = document.createElement("p");
    variation.className = "trend-variation";
    variation.textContent = copy.variability();
    item.append(trend, variation);
    taskResults.append(item);
  }
  if (taskResults.childElementCount) reportCard.append(taskResults);

  const note = document.createElement("p");
  note.className = "report-note";
  note.textContent = copy.reportDisclaimer;
  reportCard.append(note);
  reportCard.setAttribute("aria-busy", "false");
  renderTrack(report);
  renderAboutReport(report);
}

function renderTrack(report) {
  const target = document.querySelector("#track-card");
  if (!target) return;
  target.replaceChildren();
  const days = report.daily.slice(-30);
  const completed = days.filter((day) => day.complete).length;
  const partial = days.filter((day) => day.task_count > 0 && !day.complete).length;
  const summary = document.createElement("div");
  summary.className = "track-summary";
  [
    [completed, "days with all activities"],
    [partial, "days started but not complete"],
    [`${report.current_streak}`, "current complete-day streak"],
  ].forEach(([value, label]) => {
    const stat = document.createElement("div");
    stat.className = "track-stat";
    const strong = document.createElement("strong");
    strong.textContent = value;
    const span = document.createElement("span");
    span.textContent = label;
    stat.append(strong, span);
    summary.append(stat);
  });
  const dayGrid = document.createElement("div");
  dayGrid.className = "track-days";
  days.forEach((day) => {
    const item = document.createElement("div");
    item.className = `track-day ${day.complete ? "complete" : day.task_count ? "partial" : ""}`;
    const date = new Date(`${day.date}T00:00:00`);
    const name = document.createElement("strong");
    name.textContent = date.toLocaleDateString(currentLocale(), { weekday: "short" });
    const dateLabel = document.createElement("small");
    dateLabel.textContent = date.toLocaleDateString(currentLocale(), { month: "short", day: "numeric" });
    const status = document.createElement("span");
    status.textContent = day.complete ? "Complete" : day.task_count ? `${day.task_count}/5 done` : "Not started";
    item.setAttribute("aria-label", `${day.date}: ${status.textContent}`);
    item.append(name, dateLabel, status);
    dayGrid.append(item);
  });
  target.append(summary, dayGrid);
}

function renderAboutReport(report) {
  const target = document.querySelector("#about-report-grid");
  if (!target) return;
  target.replaceChildren();
  const activeDays = report.daily.filter((day) => day.task_count > 0).length;
  const activityDays = report.daily.filter((day) => day.task_count === 5).length;
  [
    [activeDays, "active days in the last 30 days"],
    [activityDays, "days with all five activities"],
    [report.baseline_ready ? "Ready" : "Building", "personal reference status"],
  ].forEach(([value, label]) => {
    const stat = document.createElement("div");
    stat.className = "about-report-stat";
    const strong = document.createElement("strong");
    strong.textContent = value;
    const span = document.createElement("span");
    span.textContent = label;
    stat.append(strong, span);
    target.append(stat);
  });
}

function resetActivity() {
  if (activityTimerId !== null) window.clearInterval(activityTimerId);
  for (const timeoutId of reactionTimeoutIds) window.clearTimeout(timeoutId);
  reactionTimeoutIds = [];
  activityTimerId = null;
  activityIntro.hidden = false;
  activityPlay.hidden = true;
  activityResult.hidden = true;
  recallForm.hidden = true;
  recallForm.reset();
  fluencyEntry.hidden = true;
  fluencyInput.value = "";
  spatialGrid.hidden = true;
  spatialGrid.replaceChildren();
  symbolGame.hidden = true;
  symbolChoices.replaceChildren();
  reactionGame.hidden = true;
  reactionCue.classList.remove("active");
  wordDisplay.replaceChildren();
  submitActivityButton.hidden = true;
  submitActivityButton.disabled = false;
  activeTask = null;
  activeWords = [];
  activeTargets = [];
  selectedTargets.clear();
  symbolRounds = [];
  symbolRoundIndex = 0;
  symbolCorrect = 0;
  symbolResponseTimes = [];
  reactionPlan = [];
  reactionIndex = 0;
  reactionCorrect = 0;
  reactionFalseTaps = 0;
  reactionMisses = 0;
  reactionTimes = [];
  reactionState = "waiting";
}

function shuffled(items) {
  const result = [...items];
  for (let index = result.length - 1; index > 0; index -= 1) {
    const swapIndex = Math.floor(Math.random() * (index + 1));
    [result[index], result[swapIndex]] = [result[swapIndex], result[index]];
  }
  return result;
}

function renderSpatialGrid(showTargets) {
  spatialGrid.replaceChildren();
  for (let index = 0; index < 16; index += 1) {
    const cell = document.createElement("button");
    cell.type = "button";
    cell.className = "spatial-cell";
    cell.setAttribute("aria-label", `Grid square ${index + 1}`);
    cell.dataset.index = String(index);
    if (showTargets && activeTargets.includes(index)) {
      cell.classList.add("target");
    } else if (!showTargets && selectedTargets.has(index)) {
      cell.classList.add("selected");
      cell.setAttribute("aria-pressed", "true");
    } else {
      cell.setAttribute("aria-pressed", "false");
    }
    spatialGrid.append(cell);
  }
}

function startCountdown(seconds, onComplete) {
  let remaining = seconds;
  document.querySelector("#activity-timer").textContent = "";
  activityTimerId = window.setInterval(() => {
    remaining -= 1;
    if (remaining <= 0) {
      window.clearInterval(activityTimerId);
      activityTimerId = null;
      onComplete();
    }
  }, 1000);
}

function startActivity(taskName) {
  const copy = analysisCopy[currentLanguage];
  if (!consentCheckbox.checked) {
    showStatus(translations[currentLanguage].activityConsent, true);
    return;
  }
  const expectedGame = dailySession?.session?.next?.game_id;
  const normalizedTask = taskName === "spatial_recall" ? "pattern_recall" : taskName;
  if (dailySession?.session?.next?.type === "game" && expectedGame !== normalizedTask) {
    showStatus("Please complete the current activity first.", true);
    return;
  }

  showStatus("");
  activeTask = taskName;
  activityStartedAt = Date.now();
  activityIntro.hidden = true;
  activityResult.hidden = true;
  activityPlay.hidden = false;
  recallForm.hidden = true;
  fluencyEntry.hidden = true;
  spatialGrid.hidden = true;
  symbolGame.hidden = true;
  reactionGame.hidden = true;
  submitActivityButton.hidden = true;
  submitActivityButton.disabled = false;
  selectedTargets.clear();
  wordDisplay.replaceChildren();

  if (taskName === "word_recall") {
    activeWords = dailyShuffle(activityWords[currentLanguage]).slice(0, activityWordCount());
    const recallFields = recallForm.querySelector(".recall-fields");
    recallFields.replaceChildren();
    activeWords.forEach((_, index) => {
      const label = document.createElement("label");
      const hint = document.createElement("span");
      hint.className = "sr-only";
      hint.textContent = `Word ${index + 1}`;
      const input = document.createElement("input");
      input.type = "text";
      input.maxLength = 40;
      input.autocomplete = "off";
      label.append(hint, input);
      recallFields.append(label);
    });
    document.querySelector("#activity-step").textContent = copy.recallPrompt;
    for (const word of activeWords) {
      const chip = document.createElement("span");
      chip.className = "word-chip";
      chip.textContent = word;
      wordDisplay.append(chip);
    }
    startCountdown(5, () => {
      wordDisplay.replaceChildren();
      document.querySelector("#activity-step").textContent = copy.recallAfter;
      recallForm.hidden = false;
      recallForm.querySelector("input").focus();
    });
  } else if (taskName === "category_fluency") {
    document.querySelector("#activity-step").textContent = copy.fluencyPrompt;
    fluencyInput.placeholder = copy.fluencyPlaceholder;
    fluencyEntry.hidden = false;
    fluencyInput.disabled = false;
    submitActivityButton.textContent = copy.save;
    submitActivityButton.hidden = true;
    fluencyInput.focus();
    startCountdown(60, () => {
      fluencyInput.disabled = true;
      document.querySelector("#activity-step").textContent = copy.fluencyAfter;
      submitActivityButton.hidden = false;
    });
  } else if (taskName === "spatial_recall") {
    document.querySelector("#activity-step").textContent = copy.spatialPrompt;
    activeTargets = dailyShuffle(Array.from({ length: 16 }, (_, index) => index)).slice(0, 3);
    spatialGrid.hidden = false;
    renderSpatialGrid(true);
    startCountdown(5, () => {
      document.querySelector("#activity-step").textContent = copy.spatialAfter;
      renderSpatialGrid(false);
      submitActivityButton.textContent = copy.save;
      submitActivityButton.hidden = false;
      submitActivityButton.disabled = selectedTargets.size !== 3;
    });
  } else if (taskName === "symbol_match") {
    symbolGame.hidden = false;
    document.querySelector("#activity-step").textContent = copy.symbolPrompt;
    const symbols = ["○", "△", "□", "◇"];
    const seedSymbols = dailyShuffle(symbols);
    symbolRounds = Array.from({ length: 8 + activityDifficulty() * 2 }, (_, index) => {
      const target = seedSymbols[index % seedSymbols.length];
      return { target, choices: dailyShuffle(symbols) };
    });
    symbolRoundIndex = 0;
    symbolCorrect = 0;
    symbolResponseTimes = [];
    renderSymbolRound();
  } else if (taskName === "reaction_tap") {
    reactionGame.hidden = false;
    document.querySelector("#activity-step").textContent = copy.reactionPrompt;
    document.querySelector("#reaction-instructions").textContent = copy.reactionPrompt;
    const level = activityDifficulty();
    reactionPlan = dailyShuffle([
      ...Array(5 + level).fill(true),
      ...Array(3 + level).fill(false),
    ]);
    reactionIndex = 0;
    reactionCorrect = 0;
    reactionFalseTaps = 0;
    reactionMisses = 0;
    reactionTimes = [];
    reactionState = "waiting";
    document.querySelector("#reaction-progress").textContent = "";
    scheduleReactionRound();
  }
}

function renderSymbolRound() {
  if (symbolRoundIndex >= symbolRounds.length) {
    document.querySelector("#activity-step").textContent = analysisCopy[currentLanguage].symbolAfter;
    document.querySelector("#symbol-progress").textContent = "";
    symbolTarget.textContent = "";
    symbolChoices.replaceChildren();
    submitActivityButton.textContent = analysisCopy[currentLanguage].save;
    submitActivityButton.hidden = false;
    return;
  }
  const round = symbolRounds[symbolRoundIndex];
  document.querySelector("#symbol-progress").textContent =
    `${symbolRoundIndex + 1} / ${symbolRounds.length}`;
  symbolTarget.textContent = round.target;
  symbolRoundStartedAt = performance.now();
  symbolChoices.replaceChildren();
  for (const symbol of round.choices) {
    const choice = document.createElement("button");
    choice.type = "button";
    choice.className = "symbol-choice";
    choice.dataset.symbol = symbol;
    choice.textContent = symbol;
    symbolChoices.append(choice);
  }
}

function scheduleReactionRound() {
  reactionCue.classList.remove("active");
  reactionCue.dataset.active = "false";
  if (reactionIndex >= reactionPlan.length) {
    reactionState = "finished";
    document.querySelector("#activity-step").textContent = analysisCopy[currentLanguage].reactionAfter;
    document.querySelector("#reaction-progress").textContent = "";
    submitActivityButton.textContent = analysisCopy[currentLanguage].save;
    submitActivityButton.hidden = false;
    return;
  }
  document.querySelector("#reaction-progress").textContent =
    `${reactionIndex + 1} / ${reactionPlan.length}`;
  reactionState = "waiting";
  const waitId = window.setTimeout(() => {
    const isGo = reactionPlan[reactionIndex];
    reactionState = isGo ? "go" : "no-go";
    reactionCue.classList.toggle("active", isGo);
    reactionCue.dataset.active = String(isGo);
    if (isGo) reactionCue.dataset.startedAt = String(performance.now());
    const cueId = window.setTimeout(() => {
      if (reactionState === "go") reactionMisses += 1;
      if (reactionState === "no-go") reactionCorrect += 1;
      reactionIndex += 1;
      scheduleReactionRound();
    }, 850);
    reactionTimeoutIds.push(cueId);
  }, 800 + Math.random() * 800);
  reactionTimeoutIds.push(waitId);
}

function handleReactionTap() {
  if (activeTask !== "reaction_tap" || reactionState === "finished") return;
  if (reactionState === "go") {
    reactionCorrect += 1;
    reactionTimes.push(performance.now() - Number(reactionCue.dataset.startedAt));
    reactionState = "go-tapped";
    reactionCue.classList.remove("active");
    reactionCue.dataset.active = "false";
  } else if (reactionState === "no-go") {
    reactionFalseTaps += 1;
    reactionState = "no-go-tapped";
  } else if (reactionState === "waiting") {
    reactionFalseTaps += 1;
  }
}

function median(values) {
  if (!values.length) return 0;
  const sorted = [...values].sort((left, right) => left - right);
  const middle = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
}

function cancelActivity() {
  if (activeTask && !window.confirm(analysisCopy[currentLanguage].cancelConfirm)) return;
  resetActivity();
}

function normalizeAnswer(value) {
  return value
    .trim()
    .normalize("NFKC")
    .toLocaleLowerCase()
    .replace(/[^\p{L}\p{N}\s]/gu, " ")
    .replace(/\s+/gu, " ")
    .trim();
}

async function saveActivityResult(event) {
  event?.preventDefault();
  if (!consentCheckbox.checked) {
    showStatus(translations[currentLanguage].activityConsent, true);
    return;
  }
  if (!activeTask) return;

  let score;
  let maxScore;
  let taskMetrics = {};
  if (activeTask === "word_recall") {
    const answers = [...recallForm.querySelectorAll("input")].map((input) =>
      normalizeAnswer(input.value),
    );
    score = new Set(answers.filter((answer) =>
      activeWords.some((word) => normalizeAnswer(word) === answer),
    )).size;
    maxScore = 3;
    taskMetrics.words_recalled = score;
  } else if (activeTask === "category_fluency") {
    const entries = fluencyInput.value
      .split(/[,\n;،؛]+/u)
      .map(normalizeAnswer)
      .filter(Boolean);
    score = Math.min(50, new Set(entries).size);
    maxScore = 50;
    taskMetrics.unique_entry_count = score;
  } else if (activeTask === "spatial_recall") {
    score = [...selectedTargets].filter((target) => activeTargets.includes(target)).length;
    maxScore = 3;
    taskMetrics.correct_positions = score;
  } else if (activeTask === "symbol_match") {
    score = Math.min(8, symbolCorrect);
    maxScore = 8;
    taskMetrics.correct_matches = symbolCorrect;
    taskMetrics.round_count = symbolRounds.length;
    taskMetrics.median_response_ms = median(symbolResponseTimes);
  } else {
    score = Math.min(8, reactionCorrect);
    maxScore = 8;
    taskMetrics.correct_responses = reactionCorrect;
    taskMetrics.round_count = reactionPlan.length;
    taskMetrics.median_response_ms = median(reactionTimes);
    taskMetrics.missed_cues = reactionMisses;
    taskMetrics.early_taps = reactionFalseTaps;
  }
  const durationSeconds = Math.min(600, Math.round((Date.now() - activityStartedAt) / 1000));
  submitActivityButton.disabled = true;
  const recallSubmit = document.querySelector("#submit-recall");
  if (!recallForm.hidden) recallSubmit.disabled = true;

  try {
    const url =
      activeTask === "symbol_match" || activeTask === "reaction_tap"
        ? "/api/task-results"
        : "/api/activities/attempts";
    const payload =
      url === "/api/task-results"
        ? {
            task_id: activeTask,
            score,
            max_score: maxScore,
            duration_seconds: durationSeconds,
            metrics: taskMetrics,
            consented: consentCheckbox.checked,
          }
        : {
        participant_id: participantId,
        language: currentLanguage,
        task_name: activeTask,
        score,
        max_score: maxScore,
        duration_seconds: durationSeconds,
        consented: consentCheckbox.checked,
          };
    await requestJson(url, { method: "POST", body: JSON.stringify(payload) });
    if (dailySession?.session?.next?.type === "game") {
      dailySession = await requestJson(
        `/api/sessions/${dailySession.session.date}/games/${activeTask === "spatial_recall" ? "pattern_recall" : activeTask}`,
        {
          method: "POST",
          body: JSON.stringify({
            skipped: false,
            result: { score, max_score: maxScore, duration_seconds: durationSeconds, metrics: taskMetrics },
            client_event_id: sessionEventId(),
          }),
        },
      );
    }
    const completedActivities = Number(localStorage.getItem("cogni-completed-activities") || "0");
    localStorage.setItem("cogni-completed-activities", String(completedActivities + 1));
    activityPlay.hidden = true;
    activityIntro.hidden = false;
    activityResult.textContent = analysisCopy[currentLanguage].complete();
    activityResult.hidden = false;
    recallForm.reset();
    activeWords = [];
    activeTargets = [];
    selectedTargets.clear();
    activeTask = null;
    resetActivity();
    updateActivityVisibility();
    activityResult.hidden = false;
    activityResult.textContent = analysisCopy[currentLanguage].complete();
    await loadDailyQuestion();
    updateActivityVisibility();
    loadReport().catch((error) => {
      reportCard.textContent = translations[currentLanguage].reportError;
      console.error("Unable to refresh activity report:", error);
    });
  } catch (error) {
    showStatus(translations[currentLanguage].activityError, true);
    console.error("Unable to save activity result:", error);
  } finally {
    submitActivityButton.disabled = false;
    recallSubmit.disabled = false;
  }
}

async function sendMessage(message) {
  const text = message.trim();
  if (!text) return;
  if (!consentCheckbox.checked) {
    showStatus(translations[currentLanguage].consentRequired, true);
    return;
  }
  if (!aiConsentCheckbox.checked) {
    showStatus("Enable Agent consent to send this message for a reply.", true);
    return;
  }

  sendButton.disabled = true;
  const typingIndicator = renderTypingIndicator();
  showStatus("");
  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        participant_id: participantId,
        language: currentLanguage,
        text,
        consented: consentCheckbox.checked,
        response_time_ms: Math.max(0, Math.round(performance.now() - questionShownAt)),
        typo_frequency: typedCorrections,
        repetition_count: text === lastSentText ? 1 : 0,
        typing_duration_ms: typingStartedAt === null
          ? null
          : Math.max(0, Math.round(performance.now() - typingStartedAt)),
        keypress_count: keypressCount,
        voice_duration_ms: voiceDurationMs,
        voice_pause_count: null,
        target_word_match: voiceTranscript ? voiceMatchesPracticeWord(voiceTranscript) : null,
        speech_capture_quality: voiceTranscript
          ? (voiceMatchesPracticeWord(voiceTranscript) ? "matched" : "not_matched")
          : "unavailable",
        sleep_quality: document.querySelector("#sleep-quality").value
          ? Number(document.querySelector("#sleep-quality").value)
          : null,
        illness_today: document.querySelector("#illness-today").value === ""
          ? null
          : document.querySelector("#illness-today").value === "true",
        device_type: /Mobi|Android/i.test(navigator.userAgent) ? "phone" : "desktop",
      }),
    });
    if (!response.ok) {
      let detail = "";
      try {
        const errorPayload = await response.json();
        detail = typeof errorPayload.detail === "string" ? ` ${errorPayload.detail}` : "";
      } catch {
        detail = "";
      }
      throw new Error(`Chat request failed (${response.status}).${detail}`);
    }
    const result = await response.json();
    typingIndicator.remove();
    if (dailySession?.session?.next?.type === "ask") {
      dailySession = await requestJson(
        `/api/sessions/${dailySession.session.date}/messages`,
        {
          method: "POST",
          body: JSON.stringify({
            text,
            latency_ms: Math.max(0, Math.round(performance.now() - questionShownAt)),
            typing: {
              duration_ms: typingStartedAt === null
                ? null
                : Math.max(0, Math.round(performance.now() - typingStartedAt)),
              keypress_count: keypressCount,
              corrections: typedCorrections,
            },
            client_event_id: sessionEventId(),
          }),
        },
      );
    }
    hasMessages = true;
    updateActivityVisibility();
    renderMessage(result.user_message);
    renderMessage(result.assistant_message);
    messageInput.value = "";
    lastSentText = text;
    typedCorrections = 0;
    typingStartedAt = null;
    keypressCount = 0;
    voiceDurationMs = null;
    voiceTranscript = "";
    questionShownAt = performance.now();
    messageInput.focus();
  } catch (error) {
    typingIndicator.remove();
    showStatus(error.message || translations[currentLanguage].sendError, true);
    console.error("Unable to send check-in message:", error);
  } finally {
    renderLanguage();
  }
}

function renderTypingIndicator() {
  const article = document.createElement("article");
  article.className = "message assistant-message typing-message";
  article.setAttribute("aria-label", "Cogni Checkin is typing");
  article.innerHTML = `
    <div class="assistant-avatar" aria-hidden="true">+</div>
    <div class="message-content">
      <p class="message-sender">Cogni Checkin</p>
      <div class="bubble typing-bubble" aria-hidden="true">
        <span></span><span></span><span></span>
      </div>
    </div>
  `;
  chatLog.append(article);
  chatLog.scrollTop = chatLog.scrollHeight;
  return article;
}

async function updateGeminiConsent() {
  try {
    const result = await requestJson("/api/consent/gemini", {
      method: "PUT",
      body: JSON.stringify({ consented: aiConsentCheckbox.checked }),
    });
    currentAccount.ai_consented = result.ai_consented;
    showStatus(result.ai_consented ? "Agent consent saved. You can revoke it anytime." : "Agent consent revoked.");
  } catch (error) {
    aiConsentCheckbox.checked = !aiConsentCheckbox.checked;
    showStatus(error.message, true);
  }
}

async function generateAiReport() {
  const button = document.querySelector("#generate-ai-report");
  button.disabled = true;
  aiReportSummary.hidden = false;
  aiReportSummary.textContent = "Preparing your personal activity summary…";
  try {
    const summary = await requestJson(`/api/reports/${participantId}/summary`, {
      method: "POST",
      body: JSON.stringify({}),
    });
    aiReportSummary.replaceChildren();
    const heading = document.createElement("h3");
    heading.textContent = "Agent reflection";
    aiReportSummary.append(heading);
    const sections = summary.patient_overview
      ? [
          ["Overview", summary.patient_overview],
          ["Cognitive summary", summary.cognitive_summary],
          ["Alerts and flags", summary.alerts_and_flags],
          ["Recommendations", summary.recommendations],
        ]
      : [
          ["Summary", { text: summary.summary }],
          ["Positive observations", summary.positives],
          ["Worth discussing", summary.watch_items],
        ];
    for (const [title, entries] of sections) {
      const section = document.createElement("section");
      const subheading = document.createElement("h4");
      subheading.textContent = title;
      const list = document.createElement("ul");
      const normalizedEntries = Array.isArray(entries)
        ? entries
        : Object.entries(entries).map(([key, value]) => `${key.replaceAll("_", " ")}: ${value}`);
      for (const entry of normalizedEntries) {
        const item = document.createElement("li");
        item.textContent = entry;
        list.append(item);
      }
      section.append(subheading, list);
      aiReportSummary.append(section);
    }
  } catch (error) {
    aiReportSummary.textContent = error.message;
  } finally {
    button.disabled = false;
  }
}

async function saveProfile(event) {
  event.preventDefault();
  profileStatus.textContent = "Saving…";
  const payload = Object.fromEntries(new FormData(profileForm).entries());
  payload.age = Number(payload.age);
  try {
    await requestJson("/api/profile", {
      method: "PUT",
      body: JSON.stringify(payload),
    });
    const updated = await requestJson("/api/auth/me");
    currentAccount = updated;
    updateProfileForm(updated);
    profileStatus.textContent = "Profile saved.";
  } catch (error) {
    profileStatus.textContent = error.message;
  }
}

function updateThemeButton() {
  const dark = document.body.classList.contains("dark-mode");
  darkModeButton?.setAttribute("aria-pressed", String(dark));
  darkModeButton?.setAttribute("aria-label", dark ? "Use light mode" : "Enable dark mode");
  if (darkModeButton) darkModeButton.textContent = dark ? "☀" : "◐";
}

function startVoiceInput() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    showStatus("Voice input is not available in this browser. You can type instead.", true);
    return;
  }
  if (voiceListening && voiceRecognition) {
    voiceRecognition.stop();
    return;
  }
  const recognition = new SpeechRecognition();
  voiceRecognition = recognition;
  voiceListening = true;
  const voiceButton = document.querySelector("#voice-button");
  voiceButton.setAttribute("aria-pressed", "true");
  voiceButton.classList.add("listening");
  voiceButton.setAttribute("aria-label", "Stop voice input");
  voiceStartedAt = performance.now();
  voiceTranscript = "";
  recognition.lang = { en: "en-IN", hi: "hi-IN", mr: "mr-IN" }[currentLanguage];
  recognition.interimResults = true;
  recognition.maxAlternatives = 1;
  recognition.onresult = (event) => {
    voiceDurationMs = Math.max(0, Math.round(performance.now() - voiceStartedAt));
    const transcript = [...event.results]
      .filter((result) => result.isFinal)
      .map((result) => result[0].transcript)
      .join(" ")
      .trim();
    if (!transcript) return;
    voiceTranscript = transcript;
    messageInput.value = `${messageInput.value}${messageInput.value ? " " : ""}${transcript}`;
    messageInput.focus();
    const target = voicePracticeWord();
    showStatus(
      `Voice transcription ready. Practice phrase word: “${target}”. Review it, then send when you choose.`,
    );
  };
  recognition.onerror = (event) => {
    voiceDurationMs = null;
    const message = event.error === "not-allowed"
      ? "Microphone permission was denied. You can type instead."
      : "Voice input could not be captured. You can type instead.";
    showStatus(message, true);
  };
  recognition.onend = () => {
    voiceListening = false;
    voiceRecognition = null;
    voiceButton.removeAttribute("aria-pressed");
    voiceButton.classList.remove("listening");
    voiceButton.setAttribute("aria-label", "Speak a message");
  };
  try {
    recognition.start();
    showStatus(
      `Listening… say the practice word “${voicePracticeWord()}”, then press the microphone button to stop.`,
    );
  } catch (error) {
    recognition.onend();
    showStatus("Voice input could not start. You can type instead.", true);
    console.error("Unable to start voice input:", error);
  }
}

function speakGreeting() {
  if (!("speechSynthesis" in window)) {
    showStatus("Audio playback is not available in this browser.", true);
    return;
  }
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(
    `${greetingElement.textContent} ${document.querySelector("#opening-question").textContent}`,
  );
  utterance.lang = { en: "en-IN", hi: "hi-IN", mr: "mr-IN" }[currentLanguage];
  window.speechSynthesis.speak(utterance);
}

async function deleteConversation() {
  const copy = translations[currentLanguage];
  if (!(hasMessages || hasActivityRecords) || !window.confirm(copy.clearConfirm)) return;

  clearButton.disabled = true;
  showStatus("");
  try {
    const response = await fetch(`/api/conversations/${participantId}/messages`, { method: "DELETE" });
    if (!response.ok) throw new Error(`Delete request failed (${response.status}).`);
    chatLog.querySelectorAll(".conversation-message, .assistant-followup").forEach((node) => node.remove());
    hasMessages = false;
    hasActivityRecords = false;
    resetActivity();
    reportCard.textContent = analysisCopy[currentLanguage].noData;
    updateActivityVisibility();
    clearButton.disabled = true;
    showStatus("Current chat cleared. Your account and activity history remain saved.");
  } catch (error) {
    showStatus(translations[currentLanguage].clearError, true);
    console.error("Unable to delete conversation:", error);
    renderLanguage();
  }
}

languageSelect.addEventListener("change", async () => {
  if (activityTimerId !== null) resetActivity();
  currentLanguage = languageSelect.value;
  localStorage.setItem("cogni-language", currentLanguage);
  renderLanguage();
  showStatus("");
  try {
    const profile = Object.fromEntries(new FormData(profileForm).entries());
    profile.language = currentLanguage;
    profile.age = Number(profile.age);
    await requestJson("/api/profile", { method: "PUT", body: JSON.stringify(profile) });
    currentAccount.language = currentLanguage;
    await Promise.all([loadHistory(), loadReport(), loadDailyQuestion()]);
  } catch (error) {
    showStatus(translations[currentLanguage].loadError, true);
    console.error("Unable to load conversation history:", error);
  }
});

consentCheckbox.addEventListener("change", () => {
  if (!consentCheckbox.checked && activityTimerId !== null) resetActivity();
  renderLanguage();
  showStatus("");
});

document.querySelector("#show-register").addEventListener("click", () => setAuthMode("register"));
document.querySelector("#show-login").addEventListener("click", () => setAuthMode("login"));
registerForm.addEventListener("submit", (event) => {
  event.preventDefault();
  submitAuthForm(registerForm, "/api/auth/register", true);
});
loginForm.addEventListener("submit", (event) => {
  event.preventDefault();
  submitAuthForm(loginForm, "/api/auth/login", false);
});
document.querySelector("#logout-button").addEventListener("click", async () => {
  try {
    await requestJson("/api/auth/logout", { method: "POST" });
    window.location.reload();
  } catch (error) {
    showStatus(error.message, true);
  }
});
aiConsentCheckbox.addEventListener("change", updateGeminiConsent);
profileForm.addEventListener("submit", saveProfile);
document.querySelector("#generate-ai-report").addEventListener("click", generateAiReport);
document.querySelector("#voice-button").addEventListener("click", startVoiceInput);
darkModeButton?.addEventListener("click", () => {
  document.body.classList.toggle("dark-mode");
  localStorage.setItem("cogni-theme", document.body.classList.contains("dark-mode") ? "dark" : "light");
  updateThemeButton();
});
updateThemeButton();
menuButton?.addEventListener("click", () => {
  const open = appShell.classList.toggle("sidebar-open");
  menuButton.setAttribute("aria-expanded", String(open));
  if (open) appSidebar.querySelector("a")?.focus();
});
document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape" || !appShell.classList.contains("sidebar-open")) return;
  appShell.classList.remove("sidebar-open");
  menuButton.setAttribute("aria-expanded", "false");
  menuButton.focus();
});
textSizeDecrease?.addEventListener("click", () => {
  textScaleIndex = Math.max(0, textScaleIndex - 1);
  applyTextScale();
});
textSizeIncrease?.addEventListener("click", () => {
  textScaleIndex = Math.min(textScales.length - 1, textScaleIndex + 1);
  applyTextScale();
});
chatTestButton.addEventListener("click", () => {
  showView("chat-card");
  activityCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
});
for (const link of document.querySelectorAll("[data-view]")) {
link.addEventListener("click", (event) => {
  event.preventDefault();
  showView(link.dataset.view);
  history.replaceState(null, "", `#${link.dataset.view}`);
});
}

messageForm.addEventListener("submit", (event) => {
  event.preventDefault();
  sendMessage(messageInput.value);
});
messageInput.addEventListener("keydown", (event) => {
  if (typingStartedAt === null) typingStartedAt = performance.now();
  keypressCount += 1;
  if (event.key === "Backspace" || event.key === "Delete") typedCorrections += 1;
});

clearButton.addEventListener("click", deleteConversation);
activityOptions.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-task]");
  if (button) startActivity(button.dataset.task);
});
symbolChoices.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-symbol]");
  if (!button || activeTask !== "symbol_match") return;
  if (button.dataset.symbol === symbolRounds[symbolRoundIndex].target) symbolCorrect += 1;
  symbolResponseTimes.push(performance.now() - symbolRoundStartedAt);
  symbolRoundIndex += 1;
  renderSymbolRound();
});
reactionCue.addEventListener("click", handleReactionTap);
recallForm.addEventListener("submit", saveActivityResult);
submitActivityButton.addEventListener("click", saveActivityResult);
cancelActivityButton.addEventListener("click", cancelActivity);
spatialGrid.addEventListener("click", (event) => {
  const cell = event.target.closest("button[data-index]");
  if (!cell || activeTask !== "spatial_recall" || activityTimerId !== null) return;
  const index = Number(cell.dataset.index);
  if (selectedTargets.has(index)) selectedTargets.delete(index);
  else if (selectedTargets.size < 3) selectedTargets.add(index);
  renderSpatialGrid(false);
  if (activityTimerId === null) submitActivityButton.disabled = selectedTargets.size !== 3;
});
document.querySelector("#refresh-report").addEventListener("click", () => {
  loadReport().catch((error) => {
    reportCard.setAttribute("aria-busy", "false");
    reportCard.textContent = translations[currentLanguage].reportError;
    addRetryButton(reportCard, () => loadReport().catch((retryError) => {
      reportCard.setAttribute("aria-busy", "false");
      reportCard.textContent = translations[currentLanguage].reportError;
      addRetryButton(reportCard, () => document.querySelector("#refresh-report").click());
      console.error("Unable to retry activity report:", retryError);
    }));
    console.error("Unable to load activity report:", error);
  });
});
document.querySelector("#download-report").addEventListener("click", async (event) => {
  const button = event.currentTarget;
  button.disabled = true;
  try {
    const response = await fetch(`/api/reports/${participantId}/pdf`);
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      throw new Error(payload.detail || `Report download failed (${response.status}).`);
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "cogni-routine-report.pdf";
    document.body.append(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  } catch (error) {
    showStatus(error.message, true);
  } finally {
    button.disabled = false;
  }
});
document.querySelector("#download-daily-report").addEventListener("click", async (event) => {
  const button = event.currentTarget;
  button.disabled = true;
  const today = new Date().toLocaleDateString("en-CA");
  try {
    const response = await fetch(`/api/reports/${participantId}/daily/${today}/pdf`);
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      throw new Error(payload.detail || `Daily report download failed (${response.status}).`);
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `cogni-routine-${today}.pdf`;
    document.body.append(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  } catch (error) {
    showStatus(error.message, true);
  } finally {
    button.disabled = false;
  }
});
document.querySelector("#download-weekly-report").addEventListener("click", async (event) => {
  const button = event.currentTarget;
  button.disabled = true;
  const weekEnd = new Date().toLocaleDateString("en-CA");
  try {
    const response = await fetch(`/api/reports/${participantId}/weekly/${weekEnd}/pdf`);
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      throw new Error(payload.detail || `Weekly report download failed (${response.status}).`);
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `cogni-routine-week-${weekEnd}.pdf`;
    document.body.append(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  } catch (error) {
    showStatus(error.message, true);
  } finally {
    button.disabled = false;
  }
});
document.querySelector("#print-report").addEventListener("click", () => window.print());

initializeApplication();
applyTextScale();

# grammar_spell-check
 python test.py
🚀 Starting WebSocket test...

✅ Connected to WebSocket server

📌 Welcome message received:
   Type: connection_established
   Message: Real-time grammar and spelling assistance connected

Test 1: 'What France is capital?'
📤 Sent: What France is capital?
📥 Analysis Result:
   ✏️ Grammar Correction:
      Original:  'What France is capital?'
      Corrected: 'What is the capital of France?'
      Changed:   True
   📖 Spelling Suggestions:
      'what' → ['that', 'chat', 'hat']
      'france' → ['trance', 'franc', 'frances']
      'capital' → ['capitol', 'capita', 'capitals']
   📊 Metrics:
      Processing time: 3924.27ms
      Word count: 4
      Character count: 23
--------------------------------------------------

Test 2: 'This are wrong.'
📤 Sent: This are wrong.
📥 Analysis Result:
   ✏️ Grammar Correction:
      Original:  'This are wrong.'
      Corrected: 'These is wrong.'
      Changed:   True
   📖 Spelling Suggestions:
      'wrong' → ['wong', 'prong', 'wrongs']
      'this' → ['his', 'thus', 'thin']
      'are' → ['re', 'area', 'care']
   📊 Metrics:
      Processing time: 93.14ms
      Word count: 3
      Character count: 15
--------------------------------------------------

Test 3: 'I goes to school.'
📤 Sent: I goes to school.
📥 Analysis Result:
   ✏️ Grammar Correction:
      Original:  'I goes to school.'
      Corrected: 'I go to school.'
      Changed:   True
   📖 Spelling Suggestions:
      'goes' → ['does', 'gods', 'toes']
      'school' → ['schools', 'shool', 'cool']
   📊 Metrics:
      Processing time: 76.68ms
      Word count: 4
      Character count: 17
--------------------------------------------------

Test 4: 'The cat are sleeping.'
📤 Sent: The cat are sleeping.
📥 Analysis Result:
   ✏️ Grammar Correction:
      Original:  'The cat are sleeping.'
      Corrected: 'The cat is sleeping.'
      Changed:   True
   📖 Spelling Suggestions:
      'the' → ['they', 'he', 'them']
      'are' → ['re', 'area', 'care']
      'sleeping' → ['sweeping', 'seeping', 'bleeping']
      'cat' → ['at', 'can', 'car']
   📊 Metrics:
      Processing time: 63.87ms
      Word count: 4
      Character count: 21
--------------------------------------------------

Test 5: 'teh quik brown fox'
📤 Sent: teh quik brown fox
📥 Analysis Result:
   ✏️ Grammar Correction:
      Original:  'teh quik brown fox'
      Corrected: 'The quick brown fox'
      Changed:   True
   📖 Spelling Suggestions:
      'brown' → ['crown', 'grown', 'blown']
      'teh' → ['the', 'tech', 'tel']
      'quik' → ['quick', 'quiz', 'quit']
      'fox' → ['for', 'box', 'fax']
   📊 Metrics:
      Processing time: 307.43ms
      Word count: 4
      Character count: 18
--------------------------------------------------

Test 6: 'She don't has no idea what is the problem, the documents was not being file correctly, and him and me goes to court but not knowed the rules.'
📤 Sent: She don't has no idea what is the problem, the documents was not being file correctly, and him and me goes to court but not knowed the rules.
📥 Analysis Result:
   ✏️ Grammar Correction:
      Original:  'She don't has no idea what is the problem, the documents was not being file correctly, and him and me goes to court but not knowed the rules.'
      Corrected: 'She doesn't has any idea what is the problem, the documents were not being filed correctly, and him and me goes to court but not knew the rules.'
      Changed:   True
   📖 Spelling Suggestions:
      'correctly' → ['currently', 'correct', 'corrected']
      'file' → ['files', 'film', 'five']
      'rules' → ['rule', 'roles', 'ruled']
      'she' → ['the', 'he', 'see']
      'knowed' → ['snowed', 'knower', 'know']
      'him' → ['his', 'hit', 'jim']
      'court' → ['count', 'courts', 'curt']
      'and' → ['an', 'any', 'add']
      'idea' → ['ideas', 'ideal', 'ida']
      'was' → ['as', 'has', 'way']
      'the' → ['they', 'he', 'them']
      'problem' → ['problems', 'probe', 'probes']
      'not' → ['no', 'now', 'non']
      'being' → ['bring', 'beings', 'boeing']
      'don' → ['on', 'do', 'down']
      'what' → ['that', 'chat', 'hat']
      'documents' → ['document', 'documented', 'monuments']
      'has' → ['as', 'was', 'his']
      'goes' → ['does', 'gods', 'toes']
      'but' → ['out', 'buy', 'put']
   📊 Metrics:
      Processing time: 132.8ms
      Word count: 29
      Character count: 141
--------------------------------------------------

Testing ping-pong mechanism:
📤 Sent ping
📥 Received pong successfully

✅ All tests completed successfully!
@prem-cre ➜ /workspaces/grammar_spell-check (main) $ 
#!/bin/bash
cd /sandboxes/$EXECUTION_ID || { echo "No such dir"; exit 1; }

START=$(date +%s%3N)

g++ main.cpp -o main.out 2> error.txt || exit 1

timeout 2s ./main.out < input.txt > output.txt 2>> error.txt
EXIT_CODE=$?

END=$(date +%s%3N)
DURATION=$((END - START))  # Duration in ms

echo "$DURATION" > time.txt

if [ $EXIT_CODE -eq 124 ]; then
  echo "TIME_LIMIT_EXCEEDED" > error.txt
fi
# #include <iostream>                                       
# #include <vector>                                                      
# #include <string>                                                      
# #include <sstream>
# #include <nlohmann/json.hpp>                                           
                                                                       
# using namespace std;
# using json = nlohmann::json;                                           
                                                                       
# vector<pair<string, long long>> parse_input() {
#     string input;                                                      
#     getline(cin, input);                                               
#     json jsonData = json::parse(input);
                                                                       
#     vector<pair<string, long long>> testcases;                         
#     for (const auto& item : jsonData) {                                
#         string s = item["s"];
#         long long k = item["k"];                                       
#         testcases.emplace_back(s, k);                                  
#     }                                                                  
#     return testcases;
# }                                                                      
                                                                       
# #include <iostream>
# #include <string>                                                      
# using namespace std;                                                   
                                                                       
# class Solution {
# public:                                                                
#     char processStr(const string& s, long long k) {                    
#         string result;
#         for (char ch : s) {                                            
#             if (islower(ch)) {                                         
#                 result.push_back(ch);
#             } else if (ch == '*') {                                    
#                 if (!result.empty()) result.pop_back();                
#             } else if (ch == '#') {
#                 result += result;                                      
#             } else if (ch == '%') {                                    
#                 reverse(result.begin(), result.end());                 
#             }
#         }                                                              
#     }
# };
# #include <fstream>
# #include <nlohmann/json.hpp>
# using json = nlohmann::json;
# int main() {
#     Solution sol;
#     auto testcases = parse_input();
#     json results = json::array();
#     for (const auto& testcase : testcases) {
#         string s = testcase.first;
#         long long k = testcase.second;
#         auto result = sol.processStr(s, k);
#         json result_entry;
#         result_entry["value"] = result;
#         result_entry["type"] = typeid(result).name();
#         results.push_back(result_entry);
#     }
#     std::ofstream outfile("results.txt");
#     outfile << results;
#     outfile.close();
#     return 0;
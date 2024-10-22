#include <Trade\Trade.mqh>

//+------------------------------------------------------------------+
//| Script program start function                                    |
//+------------------------------------------------------------------+
void OnStart()
{
   // Get the local time as a string and format it
   string localTime = TimeToString(TimeLocal(), TIME_DATE | TIME_SECONDS);
   StringReplace(localTime, ":", ".");
   StringReplace(localTime, " ", ".");

   // Construct the file name using the formatted time string
   string fileName = StringConcatenate("-", localTime, "-Get_All_Symbols.txt");

   // Open the file for writing
   int fileHandle = FileOpen(fileName, FILE_WRITE | FILE_ANSI | FILE_TXT);

   // Check if the file was opened successfully
   if (fileHandle == INVALID_HANDLE)
   {
      Print("Failed to open file for writing: ", fileName);
      return;
   }

   // Write all symbol names to the file
   int totalSymbols = SymbolsTotal(false);
   for (int i = 0; i < totalSymbols; i++)
   {
      string symbolName = SymbolName(i, false);
      FileWrite(fileHandle, symbolName);
   }

   // Close the file and print a success message
   FileClose(fileHandle);
   Print("File written successfully: ", fileName);
}

// The provided MQL5 script is designed to generate
// a text file containing the names of all available
// symbols in the trading terminal.

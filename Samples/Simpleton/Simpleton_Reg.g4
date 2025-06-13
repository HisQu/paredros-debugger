grammar Simpleton_Reg;

startRule : EINS+ | zwoelf | DREI DREI | EINS ZWEI DREI;
zwoelf : EINS (ZWEI |DREI)+;

// Lexer Rules for tags
EINS : '1' ;
ZWEI : '2' ;
DREI : '3' ;
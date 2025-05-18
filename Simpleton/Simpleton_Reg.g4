grammar Simpleton_Reg;

startRule : EINS+ | zwoelf | DREI DREI | EINS ZWEI DREI;
zwoelf : EINS (ZWEI |DREI)+;

// Lexer Rules for tags
EINS : '1' ;
ZWEI : '2' ;
DREI : '3' ;

// valid words of this grammar are:
//   {1^n | n in N} // EINS+
// ∪ {1u | u in {2,3}* \ λ} // zwoelf
// ∪ {33, 123} // DREI DREI, EINS ZWEI DREI

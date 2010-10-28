procedure p();
var
  a: array[1..10] of integer;
  b: array[0..9] of real;
begin
  a[5] := 10;
  a[8] := 26;
  writeln(a[5]);
  writeln(a[8]);
  b[2] := 10 / 0.5;
  b[7] := 1 * 0.5;
  writeln(b[2]);
  writeln(b[7]);
end;

begin
  p();
end.
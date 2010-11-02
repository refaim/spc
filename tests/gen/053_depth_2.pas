procedure P1(a: Real);
begin
  Writeln(a + 1);
end;

procedure P2(a: Integer);
begin
  P1(a);
end;

begin
  P2(3);
end.


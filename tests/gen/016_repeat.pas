var
  i: integer;
begin
  i := 10;
  repeat begin
    writeln(i);
    i := i - 1;
  end;
  until i = 0;
end.
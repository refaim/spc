var
  i, j: integer;
begin
  i := 10;
  j := 0;
  repeat begin
    writeln(i);
    writeln(j);
    i := i - 1;
    j := j + 1;
  end;
  until (i = 0) and (j = 10);
end.
var i: integer;
begin
  i := 1;
  repeat begin
    write(-i);
    i := i - 1;
    continue;
    write(i);
  end;
  until i = 0;
end.
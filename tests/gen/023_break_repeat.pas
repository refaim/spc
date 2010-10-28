var i: integer;
begin
  i := 1;
  repeat begin
    write(i);
    i := i - 1;
    break;
    write(-i);
  end;
  until i = 0;
end.
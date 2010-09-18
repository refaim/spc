var
  r1: record
    f1: integer;
    r2: record
      f2: integer;
      r3: record
        f3: integer;
      end;
    end;
  end;

function f(i: integer): real;
begin
end;

begin
  r1.f1 := f(f(r1.f1 + r1.r2.f2) + r1.r2.r3.f3);
end.
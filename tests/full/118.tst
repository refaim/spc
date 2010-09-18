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
begin
  r1.r2.r3.f3;
end.
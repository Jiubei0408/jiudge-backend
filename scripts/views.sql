create view contest_ac_cnt_view
as
select username,
       contest_id,
       (
           select count(distinct problem_id)
           from submission s
           where s.result in (select acceptable_results.result from acceptable_results)
             and s.username = ucr.username
             and s.contest_id = ucr.contest_id
       ) ac_cnt
from user_contest_rel ucr;

create view earliest_accept_time_view
as
select username, contest_id, problem_id, min(submit_time) accept_time
from submission s
where s.result in (select result from acceptable_results)
  and exists(
        select *
        from user_contest_rel
        where contest_id = s.contest_id
          and username = s.username
    )
group by username, contest_id, problem_id;

create view before_accept_cnt_view
as
select username, problem_id, contest_id, count(*) attempt_cnt
from submission s
where ifnull(submit_time < (
    select accept_time
    from earliest_accept_time_view earliest
    where earliest.username = s.username
      and earliest.problem_id = s.problem_id
      and earliest.contest_id = s.contest_id
), true)
  and result not in (select result from ignorable_results)
  and exists(
        select *
        from user_contest_rel
        where contest_id = s.contest_id
          and username = s.username
    )
group by username, problem_id, contest_id;

create view penalty_for_rejected_submission
as
select contest_id, username, problem_id, 20 * attempt_cnt penalty
from before_accept_cnt_view
where exists(
              select *
              from submission
              where submission.result in (select * from acceptable_results)
                and submission.username = before_accept_cnt_view.username
                and submission.problem_id = before_accept_cnt_view.problem_id
                and submission.contest_id = before_accept_cnt_view.contest_id
          )
group by contest_id, username, problem_id;

create view penalty_for_accepted_submission
as
select username,
       contest_id,
       problem_id,
       ifnull(time_to_sec(timediff(accept_time, (select start_time
                                                 from contest
                                                 where id = contest_id))) div 60,
              0) penalty
from earliest_accept_time_view
group by contest_id, problem_id, username;

create view total_penalty
as
select username,
       contest_id,
       ifnull((
                  select sum(penalty)
                  from penalty_for_accepted_submission
                  where username = ucr.username
                    and contest_id = ucr.contest_id
              ), 0)
           +
       ifnull((
                  select sum(penalty)
                  from penalty_for_rejected_submission
                  where username = ucr.username
                    and contest_id = ucr.contest_id
              ), 0) penalty
from user_contest_rel ucr
group by username, contest_id;

create view contest_statistics
as
select username,
       contest_id,
       (
           select ac_cnt
           from contest_ac_cnt_view
           where contest_id = ucr.contest_id
             and username = ucr.username
       ) ac_cnt,
       (
           select penalty
           from total_penalty
           where contest_id = ucr.contest_id
             and username = ucr.username
       ) penalty
from user_contest_rel ucr;

create view first_blood
as
select *
from earliest_accept_time_view a
where accept_time <= all (
    select accept_time
    from earliest_accept_time_view
    where problem_id = a.problem_id
      and contest_id = a.contest_id
);
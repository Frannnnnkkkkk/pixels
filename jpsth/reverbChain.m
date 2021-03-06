load('reverb2nd.mat')
load('reg_keep.mat')
arrow2set=unique(reg_2nd,'rows');
ckeepsel=ismember(arrow2set(:,1),find(ckeep)) & ismember(arrow2set(:,2),find(ckeep));
arrow2set=arrow2set(ckeepsel,:);
arrow2count=zeros(length(arrow2set),1);
for i=1:length(arrow2set)
    arrow2count(i)=nnz(all(reg_2nd==arrow2set(i,:),2));
end
load('pair_mat_duo_6s_1_2.mat')
arrow2pair=zeros(length(arrow2set),1);
for i=1:length(arrow2set)
    arrow2pair(i)=pair_mat(arrow2set(i,2),arrow2set(i,1));
end
pair_sel=arrow2pair>40;
arrow2ratio=arrow2count(pair_sel)./arrow2pair(pair_sel);
[~,I]=sort(arrow2ratio,'descend');
arrow2set=arrow2set(pair_sel,:);
result=cell(length(arrow2set),2);
for i=1:length(arrow2set)
    result{i,1}=sprintf('%s->%s',reg_set{arrow2set(I(i),1)},reg_set{arrow2set(I(i),2)});
end
result(:,2)=mat2cell(arrow2ratio(I),ones(length(arrow2set),1));

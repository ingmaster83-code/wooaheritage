require 'json'

module Jekyll
  class InfoPageGenerator < Generator
    safe true
    priority :normal

    def generate(site)
      items = load_json(site, '_rawdata/info.json')

      Jekyll.logger.info "InfoGenerator:", "#{items.size}개 관광안내소 페이지 생성 중..."
      items.each do |i|
        next if i['slug'].to_s.strip.empty?
        site.pages << InfoPage.new(site, i)
      end

      Jekyll.logger.info "InfoGenerator:", "완료 (#{items.size}개)"
    end

    private

    def load_json(site, path)
      file = File.join(site.source, path)
      return [] unless File.exist?(file)
      JSON.parse(File.read(file, encoding: 'utf-8'))
    rescue => e
      Jekyll.logger.warn "InfoGenerator:", "#{path} 로드 실패: #{e.message}"
      []
    end
  end

  class InfoPage < Page
    def initialize(site, i)
      @site = site
      @base = site.source
      @dir  = "info/#{i['slug']}"
      @name = 'index.html'

      self.process(@name)
      self.read_yaml(File.join(@base, '_layouts'), 'info.html')
      self.data.merge!(i)
      self.data['layout']      = 'info'
      self.data['title']       = build_title(i)
      self.data['description'] = build_desc(i)
    end

    private

    def build_title(i)
      loc = [i['doShort'], i['sigungu']].compact.join(' ')
      "#{i['infoName']} #{loc} 위치·운영시간 안내"
    end

    def build_desc(i)
      loc = [i['doShort'], i['sigungu']].compact.join(' ')
      intro = (i['intro'] || '').gsub(/\s+/, ' ')
      "#{loc} #{i['infoName']}. #{intro}"[0, 155]
    end
  end
end
